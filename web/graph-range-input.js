import {latexInput,parse} from './parser.js';

const unaryFunctions = {
  abs: Math.abs, sqrt: Math.sqrt, cbrt: Math.cbrt, exp: Math.exp, ln: Math.log,
  sin: Math.sin, cos: Math.cos, tan: Math.tan, asin: Math.asin, acos: Math.acos, atan: Math.atan
};

function rangeValue(tree) {
  const op = tree.value;
  if (tree.kind === 'number') return Number(op);
  if (tree.kind === 'symbol') return op === 'pi' ? Math.PI : op === 'e' ? Math.E : NaN;
  const args = tree.args.map(rangeValue);
  if (!args.every(Number.isFinite)) return NaN;
  const [a,b] = args;
  switch (tree.kind) {
    case 'group': return a;
    case 'unary': return op === '-' ? -a : a;
    case 'binary':
      switch (op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/': return a / b;
        case '^': return a ** b;
        default: return NaN;
      }
    case 'call':
      if (op === 'log' && args.length === 2 && b > 0 && b !== 1) return Math.log(a) / Math.log(b);
      if (op === 'log' && args.length === 1) return Math.log10(a);
      if (args.length === 1 && Object.hasOwn(unaryFunctions,op)) return unaryFunctions[op](a);
  }
  return NaN;
}

export function parseGraphRangeInput(source) {
  if (!source.trim()) return null;
  const number = Number(source);
  if (Number.isFinite(number)) return {value:number};
  try {
    const tree = parse(latexInput(source));
    const value = rangeValue(tree);
    return Number.isFinite(value) ? {value,tree} : null;
  } catch {
    return null;
  }
}
