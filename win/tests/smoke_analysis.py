"""Exercise catalog -> registration -> analysis using isolated portable app state."""
import argparse
import json
import pathlib
import queue
import shutil
import subprocess
import tempfile
import threading


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('cli',type=pathlib.Path)
    args=parser.parse_args()
    original=args.cli.resolve()
    checks=0
    with tempfile.TemporaryDirectory(prefix='symvacas-analysis-') as directory:
        root=pathlib.Path(directory)
        cli=root/original.name
        shutil.copyfile(original,cli)
        # A separate registry and runtime folder leave the user's saved datasets untouched.
        shutil.copytree(original.parent/'python_embeded',root/'python_embeded',ignore=shutil.ignore_patterns('__pycache__','_symvacas'))
        def run(*command,source=None,success=True):
            nonlocal checks
            proc=subprocess.run([str(cli),*command],input=source,capture_output=True,text=True,encoding='utf-8',timeout=120)
            assert (proc.returncode==0)==success,(command,proc.stdout,proc.stderr)
            result=json.loads(proc.stdout);checks+=1
            return result
        catalog=run('catalog','ttest2')
        hit=catalog['results'][0]
        assert hit['name']=='ttest2' and hit['signature'] and hit['descriptionKo'] and hit['examples'],hit
        assert run('catalog','회귀')['total']>0
        survival_rows=[[1,1,1],[2,1,2],[3,0,1],[4,1,2],[5,1,1],[6,0,2],[7,1,2],[8,1,1]]
        survival_catalog=run('catalog','survivalanalysis')['results'][0]
        assert survival_catalog['signature']=='survivalanalysis(data,coxEnabled,ties,entryColumn,phCheck)'
        assert survival_catalog['arguments'][1]['name']=='coxEnabled'
        cox_catalog=run('catalog','cox')['results'][0]
        assert cox_catalog['signature']=='cox(data,ties,entryColumn,phCheck)'
        cox_fit=run('stats','survivalanalysis(data,1,efron,-1,1)','--data','-',source=json.dumps(survival_rows))
        assert 'error' not in cox_fit['survival']['cox'] and cox_fit['survival']['ph'],cox_fit
        swapped=run('stats','survivalanalysis(data,efron,1,-1,1)','--data','-',source=json.dumps(survival_rows),success=False)
        assert 'argument 2 (coxEnabled)' in swapped['error'] and survival_catalog['signature'] in swapped['error']
        found=run('stats',hit['examples'][0]['expression'])
        assert found['ok'] and found.get('statisticsReport'),found
        assert run('dataset','list')['datasets']==[]
        assert run('dataset','save','cohort','-','--format','json',source='[1,2,3,4]')['ok']
        assert run('dataset','show','cohort')['source']=='1\n2\n3\n4'
        assert run('eval','mean(cohort)')['exact']=='5/2'
        assert run('stats','stats(cohort)')['statisticsReport']
        assert run('dataset','save','cohort','-','--format','csv',source='8\n10',success=False)['ok'] is False
        assert run('dataset','save','cohort','-','--format','csv','--replace',source='8\n10')['ok']
        assert run('stats','mean(cohort)')['exact']=='9'
        assert run('dataset','save','trial','-','--format','csv',source='x,y\n1,3\n2,5\n3,7\n4,9\n5,11')['kind']=='xy'
        fit=run('stats','regression(trial,linear)')
        assert fit['ok'] and fit['regression'] and fit['statisticsCopyReport'],fit
        large=list(range(1,3001))
        assert run('stats','mean(data)','--data','-',source=json.dumps(large))['exact']=='3001/2'
        assert run('stats','ttest2(0,a,b)','--data','-',source=json.dumps({'a':[1,2,3,4,5],'b':[2,4,6,8,10]}))['statisticsReport']
        assert run('stats','anova(a,b,c)','--data','-',source=json.dumps({'a':[1,2,3,4],'b':[2,4,5,7],'c':[4,6,8,9]}))['statisticsReport']
        equation=run('solve','x^2-5*x+6=0')
        assert equation['ok'] and equation['equationSteps']['steps'],equation
        system=run('solve','x+y=3','x-y=1','--variables','x,y')
        assert system['ok'] and '2' in system['exact'] and '1' in system['exact'],system
        numeric=run('solve','cos(x)=x','--method','nsolve','--guess','0.5')
        assert numeric['ok'] and abs(float(numeric['decimal'])-0.739085133215)<1e-9,numeric
        ode=run('solve','diff(y(x),x)=y(x)','--method','dsolve','--variables','y(x)','--independent','x')
        assert ode['ok'] and 'exp' in ode['exact'],ode
        mcp=subprocess.Popen([str(cli),'mcp'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',bufsize=1)
        messages=queue.Queue()
        threading.Thread(target=lambda:[messages.put(line) for line in mcp.stdout],daemon=True).start()
        ident=0
        def request(method,params=None):
            nonlocal checks,ident
            ident+=1;mcp.stdin.write(json.dumps({'jsonrpc':'2.0','id':ident,'method':method,'params':params or {}})+'\n');mcp.stdin.flush()
            result=json.loads(messages.get(timeout=60));assert result['id']==ident,result
            checks+=1;assert 'error' not in result,result
            return result['result']
        def tool(name,arguments,success=True):
            result=request('tools/call',{'name':name,'arguments':arguments})
            assert result['isError'] is (not success),result
            return json.loads(result['content'][0]['text'])
        try:
            initialized=request('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'analysis-smoke','version':'1'}})
            assert 'get_usage' in initialized['instructions'] and 'No skill' in initialized['instructions']
            mcp.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n');mcp.stdin.flush()
            metadata={item['name']:item for item in request('tools/list')['tools']}
            guide=tool('get_usage',{'section':'all'})['text']
            assert 'save_statistics_dataset' in guide and 'statisticsReport' in guide and 'initialGuess' in guide
            # Execute arguments discovered only through MCP metadata, without loading SKILL.md.
            assert tool('statistics',metadata['statistics']['inputSchema']['examples'][0])['statisticsReport']
            assert tool('solve_equations',metadata['solve_equations']['inputSchema']['examples'][0])['equationSteps']['steps']
            assert any(item['uri']=='symvacas://guide' for item in request('resources/list')['resources'])
            assert '## Statistics' in request('resources/read',{'uri':'symvacas://guide'})['contents'][0]['text']
            discovered=tool('search_catalog',{'query':'regression','limit':3})
            assert discovered['results'][0]['signature']
            survival_help=tool('search_catalog',{'query':'survivalanalysis'})['results'][0]
            assert survival_help['arguments'][3]['name']=='entryColumn'
            assert 'search_catalog' in tool('get_usage',{'section':'statistics'})['text']
            suite=tool('statistics',{'expression':'survivalanalysis(data,1,efron,-1,1)','datasets':{'data':survival_rows}})
            assert 'error' not in suite['survival']['cox'] and suite['survival']['ph'],suite
            wrong=tool('statistics',{'expression':'cox(data,1,efron,-1,1)','datasets':{'data':survival_rows}},success=False)
            assert cox_catalog['signature'] in wrong['error'] and 'no coxEnabled flag' in wrong['error']
            assert {item['name'] for item in tool('list_statistics_datasets',{})['datasets']}=={'cohort','trial'}
            assert tool('get_statistics_dataset',{'name':'cohort'})['source'].splitlines()==['8','10']
            assert tool('save_statistics_dataset',{'name':'control','data':[2,3,4,5,6]})['ok']
            assert tool('statistics',{'expression':'ttest2(0,cohort,control)'})['statisticsReport']
            assert tool('statistics',{'expression':'mean(data)','datasets':{'data':large}})['exact']=='3001/2'
            assert tool('evaluate',{'expression':'mean(control)'})['exact']=='4'
            assert tool('solve_equations',{'equations':['x+y=3','x-y=1'],'variables':['x','y']})['equationSteps']['steps']
            assert tool('solve_equations',{'equations':'cos(x)=x','method':'nsolve','initialGuess':0.5})['ok']
            tool('save_statistics_dataset',{'name':'control','data':[99]},success=False)
            tool('solve_equations',{'equations':'x=1','variables':['x','x']},success=False)
        finally:
            mcp.stdin.close()
            try:mcp.wait(timeout=10)
            except subprocess.TimeoutExpired:mcp.kill();mcp.wait()
        assert run('stats','mean(control)')['exact']=='4','MCP registration persists for subsequent CLI processes'
        persisted=json.loads((root/'data/statistics-datasets.json').read_text(encoding='utf-8'))
        assert set(persisted['datasets'])=={'cohort','trial','control'}
    print(f'{checks} native catalog / statistics / equation / registered-data checks passed')


if __name__=='__main__':
    main()
