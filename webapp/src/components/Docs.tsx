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
    setTimeout(() => {
      if (iframeRef.current != null) {
        iframeRef.current.contentDocument.querySelectorAll('a')
        .forEach(function (elem) {
          elem.setAttribute('target', '_blank');
        });
      }
    }, 5000);
  };

  // pull the Tana Publish content via our proxy
  // so that the <base target="_blank"> element can be added
  return (
    <div className='home-container'>
      {!isMounted &&
        <div className="spinner-container">
          <div className="spinner">
            <CircularProgress />
          </div>
        </div>}
      <object className='tana-publish'
        ref={iframeRef}
        name='tana-publish'
        // data="https://tana.pub/EufhKV4ZMH/tana-helper"
        data="http://localhost:8000/EufhKV4ZMH/tana-helper/"
        onLoad={handleIframeLoad} />
    </div>
  );
}
