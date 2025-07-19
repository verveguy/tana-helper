"use client";
import { JSX, useEffect } from "react";
import { scan } from "react-scan";

/**
 * ReactScan Component
 *
 * This component integrates react-scan library to enable scanning and monitoring
 * of React components in development. It initializes the scanner on mount and
 * renders nothing visually.
 *
 * The scanner helps with:
 * - Performance monitoring
 * - Component tree visualization
 * - Development debugging
 *
 * Note: This should only be included in development builds as it adds
 * monitoring overhead.
 */

export function ReactScan(): JSX.Element {
  useEffect(() => {
    // Only enable react-scan in development mode
    if (process.env.NODE_ENV === 'development') {
      scan({
        enabled: true,
      });
    }
  }, []);

  return <></>;
}
