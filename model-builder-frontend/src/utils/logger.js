const isProd = typeof import.meta !== 'undefined' && Boolean(import.meta.env && import.meta.env.PROD);

function maskSessionValues(obj) {
  try {
    const seen = new WeakSet();
    const deepClone = (value) => {
      if (value && typeof value === 'object') {
        if (seen.has(value)) return '[Circular]';
        seen.add(value);
        if (Array.isArray(value)) return value.map(deepClone);
        const out = {};
        for (const k of Object.keys(value)) {
          if (/session(_|-)?id|session/id|session/i.test(k)) {
            out[k] = '[REDACTED]';
          } else {
            out[k] = deepClone(value[k]);
          }
        }
        return out;
      }
      if (typeof value === 'string') {
        // redact UUIDs and common session patterns inside strings
        return value.replace(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, '[REDACTED]').replace(/session[_-]?id=\w+/gi, 'session_id=[REDACTED]');
      }
      return value;
    };

    return deepClone(obj);
  } catch (e) {
    return obj;
  }
}

function sanitizeArgs(args) {
  return args.map((a) => {
    if (a && typeof a === 'object') return maskSessionValues(a);
    if (typeof a === 'string') return maskSessionValues(a);
    return a;
  });
}

const logger = {
  debug: (...args) => {
    if (isProd) return; // no debug logs in production
    console.debug(...sanitizeArgs(args));
  },
  info: (...args) => {
    if (isProd) return;
    console.info(...sanitizeArgs(args));
  },
  warn: (...args) => {
    console.warn(...sanitizeArgs(args));
  },
  error: (...args) => {
    console.error(...sanitizeArgs(args));
  },
};

export default logger;
