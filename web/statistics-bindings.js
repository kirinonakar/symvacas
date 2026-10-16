import {csvRows,statisticsDatasetSource,statisticsColumnCount,statisticsKindForColumns} from './workspace-commands.js';
import {statisticsRequest} from './statistics-request.js';

// Resolve only referenced datasets, including references in stored formulas/functions.
export function savedStatisticsDatasets(tree,{datasets={},datasetKinds={},variables={},functions={}}={}){
  const result={},visited=new Set();
  function visit(node,bound=new Set()){
    if(!node)return;
    const name=node.value;
    if(node.kind==='symbol'&&!bound.has(name)){
      const key=`symbol:${name}`;if(visited.has(key))return;visited.add(key);
      if(Object.hasOwn(datasets,name)){
        const kind=statisticsColumnCount(datasetKinds[name])?datasetKinds[name]:statisticsKindForColumns(csvRows(datasets[name])[0].length);
        const literal=statisticsDatasetSource(datasets[name],kind),input=statisticsRequest(literal);
        result[name]=input.statisticsDatasets[input.tree.value]??input.tree.args.map(cell=>cell.kind==='list'?cell.args:cell);
      }else if(Object.hasOwn(variables,name))visit(variables[name],bound);
    }
    if(node.kind==='call'&&Object.hasOwn(functions,name)&&!visited.has(`call:${name}`)){
      visited.add(`call:${name}`);const definition=functions[name];visit(definition.body,new Set(definition.parameters));
    }
    for(const child of node.args||[])visit(child,bound);
  }
  visit(tree);return result;
}
