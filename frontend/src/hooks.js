import { useState } from "react";

/** Small hook to run an async API call with loading/error/result state. */
export function useRequest(fn) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const run = async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fn(...args);
      setData(res ?? {});
      return res;
    } catch (e) {
      setError(e);
      return null;
    } finally {
      setLoading(false);
    }
  };
  return { loading, error, data, run, reset: () => { setData(null); setError(null); } };
}
