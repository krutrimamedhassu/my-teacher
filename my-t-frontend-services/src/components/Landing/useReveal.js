import { useEffect, useRef, useState } from 'react';

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Triggers once when the element crosses the threshold; returns {ref, visible}.
// Honors prefers-reduced-motion by being visible immediately.
export const useReveal = ({ threshold = 0.2, rootMargin = '0px 0px -10% 0px' } = {}) => {
  const ref = useRef(null);
  const [visible, setVisible] = useState(prefersReducedMotion());

  useEffect(() => {
    if (prefersReducedMotion()) return undefined;
    const node = ref.current;
    if (!node) return undefined;
    if (typeof IntersectionObserver === 'undefined') {
      setVisible(true);
      return undefined;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setVisible(true);
            obs.disconnect();
          }
        });
      },
      { threshold, rootMargin }
    );
    obs.observe(node);
    return () => obs.disconnect();
  }, [threshold, rootMargin]);

  return { ref, visible };
};

export const revealStyle = (visible, { delay = 0, distance = 24 } = {}) => ({
  opacity: visible ? 1 : 0,
  transform: visible ? 'translateY(0)' : `translateY(${distance}px)`,
  transition: `opacity 700ms cubic-bezier(0.22, 1, 0.36, 1) ${delay}ms, transform 700ms cubic-bezier(0.22, 1, 0.36, 1) ${delay}ms`,
  willChange: 'opacity, transform',
});
