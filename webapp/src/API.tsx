import React, { Component, useEffect } from "react";
import './Home.css'

export default function API() {

  useEffect(() => {
    (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'scroll');

    return () => {
      (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'hidden');
    }

  }, []);

  return (
    <div className='home-container'>
      <iframe className = 'tana-publish' src="/rapidoc" />
    </div>
  );
}
