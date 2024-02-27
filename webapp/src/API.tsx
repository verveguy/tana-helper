import React, { Component, useEffect } from "react";
import 'rapidoc';

/* This component simply redirects us to a different site */
export default function API() {

  useEffect(() => {
    (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'scroll');

    return () => {
      (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'hidden');
    }

  }, []);

  return (
    <div className='home-container'>
      <rapi-doc spec-url="/openapi.json" />
    </div>
  );
}
