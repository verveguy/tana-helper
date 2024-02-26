import React, { Component, useEffect } from "react";
import './Home.css'

export default function Home() {

  useEffect(() => {
    (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'scroll');

    return () => {
      (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'hidden');
    }

  }, []);

  return (
    <div className='home-container'>
      <iframe className = 'tana-publish' src="https://tana.pub/EufhKV4ZMH/tana-helper" />
    </div>
  );
}
