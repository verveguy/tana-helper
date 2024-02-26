
import { useEffect, useState } from "react";

/* observe changes in the window sizing */
export function useWindowSize() {
  // Initialize state with undefined width/height so server and client renders match
  // Learn more here: https://joshwcomeau.com/react/the-perils-of-rehydration/
  const [windowSize, setWindowSize] = useState({
    windowWidth: undefined,
    windowHeight: undefined
  });

  useEffect(() => {
    // Handler to call on window resize
    function handleResize() {
      // Set window width/height to state
      setWindowSize({
        windowWidth: window.innerWidth,
        windowHeight: window.innerHeight
      });
    }

    // Add event listener
    window.addEventListener("resize", handleResize);

    // Call handler right away so state gets updated with initial window size
    handleResize();

    // Remove event listener on cleanup
    return () => window.removeEventListener("resize", handleResize);
  }, []); // Empty array ensures that effect is only run on mount

  return windowSize;
}


/* observe changes in the container sizing */
export function useDimensions(containerRef: React.MutableRefObject<null>) {
  const [dimensions, setDimensions] = useState({
    width: undefined,
    height: undefined,
  });
  
  useEffect(() => {
    if (!containerRef || !containerRef.current) return;
    const resizeObserver = new ResizeObserver(() => {
      setDimensions({
        width: containerRef.current.offsetWidth,
        height: containerRef.current.offsetHeight,
      });
    });
    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect(); // clean up 
  }, [containerRef]);

  return dimensions;
}


