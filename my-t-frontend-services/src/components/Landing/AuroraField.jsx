import React, { useEffect, useRef } from 'react';
import { colors, shaderPalette } from './tokens';

// -------- shader sources --------

const VERT = `#version 300 es
precision highp float;
layout(location=0) in vec2 a_pos;
out vec2 v_uv;
void main() {
  v_uv = a_pos * 0.5 + 0.5;
  gl_Position = vec4(a_pos, 0.0, 1.0);
}`;

// Volumetric blue-ink shader.
// Multi-octave domain-warped value-noise FBM, accumulated across a few
// "z slices" so the field reads as a depth-y cloud rather than a flat pattern.
// Mouse warps the noise origin and adds a soft luminance bloom; clicks emit
// a radial pressure wave. Bayer dither at the end kills banding on dark gradients.
const FRAG = `#version 300 es
precision highp float;
in vec2 v_uv;
out vec4 outColor;

uniform float uTime;
uniform vec2 uResolution;
uniform vec2 uMouse;
uniform float uClick;
uniform vec2 uClickPos;
uniform vec3 uPalette[5];

float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float vnoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

float fbm(vec2 p) {
  float v = 0.0;
  float amp = 0.5;
  mat2 R = mat2(0.8, -0.6, 0.6, 0.8);
  for (int i = 0; i < 5; i++) {
    v += amp * vnoise(p);
    p = R * p * 2.02;
    amp *= 0.5;
  }
  return v;
}

// 2d domain warp
vec2 warp(vec2 p, float t) {
  float q1 = fbm(p + vec2(0.0, t * 0.15));
  float q2 = fbm(p + vec2(5.2, 1.3) + vec2(t * 0.12, 0.0));
  return vec2(q1, q2);
}

void main() {
  // aspect-corrected uv
  vec2 res = uResolution;
  float aspect = res.x / res.y;
  vec2 uv = v_uv;
  vec2 p = vec2(uv.x * aspect, uv.y);

  // mouse in same coord space
  vec2 m = vec2(uMouse.x * aspect, uMouse.y);
  vec2 cpos = vec2(uClickPos.x * aspect, uClickPos.y);

  float t = uTime;
  // mouse-pulled warp center; large soft offset
  vec2 mouseOffset = (m - vec2(aspect * 0.5, 0.5)) * 0.35;

  // accumulate 4 z slices for fake volumetrics
  float density = 0.0;
  for (int i = 0; i < 4; i++) {
    float fi = float(i);
    float z = t * 0.06 + fi * 0.27;
    vec2 q = p * 1.4 + mouseOffset + warp(p * 0.9 + z, t) * 0.55;
    // each slice slightly offset to read as parallax
    q += vec2(sin(t * 0.07 + fi), cos(t * 0.05 + fi)) * 0.15;
    density += fbm(q + z) * (1.0 - fi * 0.12);
  }
  density *= 0.25;

  // click ripple, radial wave centered at cpos
  float r = distance(p, cpos);
  float ripple = uClick * 0.65 * exp(-r * r * 18.0) * sin(r * 22.0 - t * 6.0);
  density += ripple;

  // mouse-only warps the noise; no luminance bloom around the cursor.
  float bloom = 0.0;

  // palette mix: deep base, midtone, brighter cobalt, ice highlights on peaks
  float d = clamp(density, 0.0, 1.5);
  vec3 col = uPalette[3]; // ink-950 base
  col = mix(col, uPalette[0], smoothstep(0.05, 0.45, d));         // ink-900
  col = mix(col, uPalette[1], smoothstep(0.30, 0.75, d));         // cobalt-700
  col = mix(col, uPalette[2], smoothstep(0.60, 1.05, d));         // cobalt-500
  col += uPalette[4] * pow(smoothstep(0.7, 1.25, d), 2.2) * 0.55; // ice highlights
  col += uPalette[4] * bloom * 0.65;
  col += uPalette[2] * uClick * exp(-r * r * 8.0) * 0.4;          // click flash

  // soft vignette
  vec2 vc = uv - 0.5;
  float vig = 1.0 - dot(vc, vc) * 0.85;
  col *= vig;

  // ordered + hash dither to kill banding on dark gradients
  float dither = (hash(gl_FragCoord.xy) - 0.5) / 255.0;
  col += dither;

  outColor = vec4(col, 1.0);
}`;

// -------- helpers --------

const compile = (gl, type, src) => {
  const sh = gl.createShader(type);
  gl.shaderSource(sh, src);
  gl.compileShader(sh);
  if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(sh);
    gl.deleteShader(sh);
    throw new Error('Shader compile error: ' + log);
  }
  return sh;
};

const link = (gl, vs, fs) => {
  const p = gl.createProgram();
  gl.attachShader(p, vs);
  gl.attachShader(p, fs);
  gl.bindAttribLocation(p, 0, 'a_pos');
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
    const log = gl.getProgramInfoLog(p);
    gl.deleteProgram(p);
    throw new Error('Program link error: ' + log);
  }
  return p;
};

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// CSS-only fallback when WebGL2 isn't available. Uses the same palette so
// the hero never looks broken; static, but still atmospheric.
const FallbackBg = () => (
  <div
    aria-hidden
    style={{
      position: 'absolute',
      inset: 0,
      background: `
        radial-gradient(120% 80% at 30% 30%, ${colors.cobalt500}55 0%, transparent 55%),
        radial-gradient(80% 60% at 75% 70%, ${colors.cobalt700}77 0%, transparent 60%),
        radial-gradient(60% 50% at 20% 80%, ${colors.ice200}22 0%, transparent 70%),
        linear-gradient(180deg, ${colors.ink950} 0%, ${colors.ink900} 50%, ${colors.ink950} 100%)
      `,
    }}
  />
);

// -------- component --------

const AuroraField = ({ containerRef }) => {
  const canvasRef = useRef(null);
  const fallbackRef = useRef(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;

    const gl = canvas.getContext('webgl2', {
      antialias: false,
      alpha: false,
      premultipliedAlpha: false,
      preserveDrawingBuffer: false,
      powerPreference: 'high-performance',
    });

    if (!gl) {
      fallbackRef.current = true;
      canvas.style.display = 'none';
      return undefined;
    }

    let program;
    try {
      const vs = compile(gl, gl.VERTEX_SHADER, VERT);
      const fs = compile(gl, gl.FRAGMENT_SHADER, FRAG);
      program = link(gl, vs, fs);
      gl.deleteShader(vs);
      gl.deleteShader(fs);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn('AuroraField: shader build failed, using fallback', err);
      fallbackRef.current = true;
      canvas.style.display = 'none';
      return undefined;
    }

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 3, -1, -1, 3]),
      gl.STATIC_DRAW
    );
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

    const loc = {
      time: gl.getUniformLocation(program, 'uTime'),
      res: gl.getUniformLocation(program, 'uResolution'),
      mouse: gl.getUniformLocation(program, 'uMouse'),
      click: gl.getUniformLocation(program, 'uClick'),
      clickPos: gl.getUniformLocation(program, 'uClickPos'),
      palette: gl.getUniformLocation(program, 'uPalette[0]'),
    };

    gl.useProgram(program);
    const paletteFlat = new Float32Array(shaderPalette.flat());
    gl.uniform3fv(loc.palette, paletteFlat);

    // -------- state --------
    const reduce = prefersReducedMotion();
    const state = {
      target: [0.5, 0.5],
      mouse: [0.5, 0.5],
      click: 0,
      clickPos: [0.5, 0.5],
      lastT: performance.now() / 1000,
      startT: performance.now() / 1000,
      running: !reduce, // when reduced, render one frame and stop
      visible: true,
      tabHidden: false,
    };

    // -------- sizing --------
    const dpr = () => Math.min(window.devicePixelRatio || 1, 2);
    const resize = () => {
      const host = canvas.parentElement;
      if (!host) return;
      const rect = host.getBoundingClientRect();
      const w = Math.max(1, Math.round(rect.width * dpr()));
      const h = Math.max(1, Math.round(rect.height * dpr()));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      gl.viewport(0, 0, w, h);
    };
    resize();
    const ro = new ResizeObserver(resize);
    if (canvas.parentElement) ro.observe(canvas.parentElement);

    // -------- pointer --------
    const hostEl = containerRef?.current || canvas.parentElement;
    const onMove = (e) => {
      if (!hostEl) return;
      const rect = hostEl.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = 1 - (e.clientY - rect.top) / rect.height;
      state.target[0] = Math.min(1, Math.max(0, x));
      state.target[1] = Math.min(1, Math.max(0, y));
    };
    const onLeave = () => {
      // ease back toward center
      state.target[0] = 0.5;
      state.target[1] = 0.5;
    };
    const onDown = (e) => {
      if (!hostEl) return;
      const rect = hostEl.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = 1 - (e.clientY - rect.top) / rect.height;
      state.clickPos[0] = x;
      state.clickPos[1] = y;
      // nudge cursor target toward click for a brief "lean-in"
      state.target[0] = x;
      state.target[1] = y;
      state.click = 1;
    };

    if (!reduce && hostEl) {
      hostEl.addEventListener('pointermove', onMove);
      hostEl.addEventListener('pointerleave', onLeave);
      hostEl.addEventListener('pointerdown', onDown);
    }

    // -------- pause when off-screen or tab hidden --------
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          state.visible = e.isIntersecting;
        });
      },
      { threshold: 0 }
    );
    if (canvas.parentElement) io.observe(canvas.parentElement);

    const onVis = () => {
      state.tabHidden = document.visibilityState === 'hidden';
    };
    document.addEventListener('visibilitychange', onVis);

    // -------- render loop --------
    let raf = 0;
    const drawOnce = () => {
      const tNow = performance.now() / 1000;
      const dt = Math.min(0.05, tNow - state.lastT);
      state.lastT = tNow;
      // smooth mouse toward target
      const k = 1 - Math.exp(-dt * 7);
      state.mouse[0] += (state.target[0] - state.mouse[0]) * k;
      state.mouse[1] += (state.target[1] - state.mouse[1]) * k;
      // decay click
      state.click *= Math.exp(-dt * 2.4);
      if (state.click < 0.001) state.click = 0;

      gl.useProgram(program);
      gl.uniform1f(loc.time, tNow - state.startT);
      gl.uniform2f(loc.res, canvas.width, canvas.height);
      gl.uniform2f(loc.mouse, state.mouse[0], state.mouse[1]);
      gl.uniform1f(loc.click, state.click);
      gl.uniform2f(loc.clickPos, state.clickPos[0], state.clickPos[1]);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    };

    const tick = () => {
      if (!state.running) return;
      if (state.visible && !state.tabHidden) drawOnce();
      raf = requestAnimationFrame(tick);
    };

    // initial draw + maybe loop
    drawOnce();
    if (state.running) raf = requestAnimationFrame(tick);

    return () => {
      state.running = false;
      cancelAnimationFrame(raf);
      ro.disconnect();
      io.disconnect();
      document.removeEventListener('visibilitychange', onVis);
      if (hostEl) {
        hostEl.removeEventListener('pointermove', onMove);
        hostEl.removeEventListener('pointerleave', onLeave);
        hostEl.removeEventListener('pointerdown', onDown);
      }
      gl.deleteBuffer(buf);
      gl.deleteProgram(program);
    };
  }, [containerRef]);

  return (
    <>
      <FallbackBg />
      <canvas
        ref={canvasRef}
        aria-hidden
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          display: 'block',
          pointerEvents: 'none',
        }}
      />
    </>
  );
};

export default AuroraField;
