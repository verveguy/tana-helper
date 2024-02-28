import React, { Component, useEffect, useRef, useState } from "react";
import './Home.css'
import { CircularProgress } from "@mui/material";

export default function Home() {
  const [isMounted, setIsMounted] = useState(false);
  const iframeRef = useRef(null);

  useEffect(() => {
    (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'scroll');

    return () => {
      (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'hidden');
    }

  }, []);

  const handleIframeLoad = () => {
    setIsMounted(true);
  };


  return (
    <div className='home-container'>
      {!isMounted &&
        <div className="spinner-container">
          <div className="spinner">
            <CircularProgress />
          </div>
        </div>}
      <iframe className='tana-publish'
        ref={iframeRef}
        src="https://tana.pub/EufhKV4ZMH/tana-helper"
        onLoad={handleIframeLoad} />
    </div>
  );
}
