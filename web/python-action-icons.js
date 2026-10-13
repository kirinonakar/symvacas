import {t} from './i18n.js';

const paths={
  "play": "M6 4 20 12 6 20Z",
  "stop": "M4 4H20V20H4Z",
  "indent": "M3 3h18v2H3V3zM9 7h12v2H9V7zM9 11h12v2H9v-2zM9 15h12v2H9v-2zM3 19h18v2H3v-2zM3 8l4 4-4 4V8z",
  "outdent": "M3 3h18v2H3V3zM9 7h12v2H9V7zM9 11h12v2H9v-2zM9 15h12v2H9v-2zM3 19h18v2H3v-2zM7 8l-4 4 4 4V8z",
  "new": "M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6zM15 5l2 2h-2V5z",
  "open": "M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zM4 6h5.17l2 2H20v2H6l-2 8V6zM6.06 18l1.5-6H20l-1.5 6H6.06z",
  "save": "M17 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z",
  "save_as": "M5 3h12l4 4v4h-2V8l-3-3H5v14h6v2H5c-1.1 0-2-.9-2-2V5c0-1.1.9-2 2-2zM7 5h8v5H7V5zM14 15l3 3-4 4h-3v-3l4-4zM15 14l3-3 3 3-3 3-3-3z",
  "cut": "M9.64 7.64c.23-.5.36-1.05.36-1.64 0-2.21-1.79-4-4-4S2 3.79 2 6s1.79 4 4 4c.59 0 1.14-.13 1.64-.36L10 12l-2.36 2.36A3.93 3.93 0 0 0 6 14c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4c0-.59-.13-1.14-.36-1.64L12 14l7 7h3v-1L9.64 7.64zM6 8c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm0 12c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zM19 3l-6 6 2 2 7-7V3h-3z",
  "copy": "M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zM19 5H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zM19 21H8V7h11v14z",
  "paste": "M19 2h-4.18C14.4.84 13.3 0 12 0S9.6.84 9.18 2H5c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM12 2c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zM19 20H5V4h2v3h10V4h2v16z"
};

export function pythonActionIcon(button,label,action) {
  button.classList.add('python-icon-action');
  button.dataset.i18narialabel=label;
  button.dataset.i18ntitle=label;
  button.setAttribute('aria-label',t(label));
  button.title=t(label);
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('viewBox','0 0 24 24');
  svg.setAttribute('aria-hidden','true');
  svg.setAttribute('focusable','false');
  const path=document.createElementNS(svg.namespaceURI,'path');
  path.setAttribute('d',paths[action]);
  svg.append(path);
  button.replaceChildren(svg);
}
