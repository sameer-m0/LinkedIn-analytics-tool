import { useEffect, useState } from "react";

interface FetchState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/** Generic data-fetching hook. ``deps`` re-runs the loader when changed. */
export function useFetch<T>(loader: () => Promise<T>, deps: unknown[]): FetchState<T> & { reload: () => void } {
  const [state, setState] = useState<FetchState<T>>({ data: null, loading: true, error: null });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let active = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    loader()
      .then((data) => active && setState({ data, loading: false, error: null }))
      .catch((err) => active && setState({ data: null, loading: false, error: String(err.message || err) }));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  return { ...state, reload: () => setNonce((n) => n + 1) };
}
