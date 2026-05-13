// Design tokens for the landing page.
// Kept in one place so the WebGL shader and the DOM/CSS can share values.

export const colors = {
  ink950: '#04060c',
  ink900: '#0a1224',
  ink700: '#1d2230',
  ink500: '#5a6071',
  cobalt700: '#1a3478',
  cobalt500: '#3460c8',
  ice200: '#b3c8ef',
  paper: '#fafaf7',
};

const hexToRgb01 = (hex) => {
  const v = parseInt(hex.slice(1), 16);
  return [((v >> 16) & 255) / 255, ((v >> 8) & 255) / 255, (v & 255) / 255];
};

// Shader palette indices used by the AuroraField fragment shader:
// 0: deep field base   (ink900)
// 1: midtone           (cobalt700)
// 2: brighter band     (cobalt500)
// 3: deepest base      (ink950)
// 4: highlights        (ice200)
export const shaderPalette = [
  hexToRgb01(colors.ink900),
  hexToRgb01(colors.cobalt700),
  hexToRgb01(colors.cobalt500),
  hexToRgb01(colors.ink950),
  hexToRgb01(colors.ice200),
];

export const ease = {
  outQuint: 'cubic-bezier(0.22, 1, 0.36, 1)',
};

// Match the chat-page greeting in ChatPage.js:1791 — system sans at very light weight.
export const fonts = {
  display: 'sans-serif',
  sans: 'sans-serif',
};
