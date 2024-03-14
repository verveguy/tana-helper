import React, { useEffect } from "react";
import './Home.css';
import { Typography } from "@mui/material";
import { Link } from "react-router-dom";

export default function Home() {
  useEffect(() => {
    (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'scroll');

    return () => {
      (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'hidden');
    }

  }, []);
  // pull the Tana Publish content via our proxy
  // so that the <base target="_blank"> element can be added
  return (
    <div className='home-container'>
      <Typography variant='h4' align='left' gutterBottom>
        Welcome to Tana Helper
      </Typography>
      <Typography variant='body1' align='left' gutterBottom>
        One of the great things about Tana is that it is able to call external systems via the <a href="https://tana.inc/docs/command-nodes#make-api-request"><code>Make API request</code></a> command. Not only can it make calls to internet services with APIs to fetch data into Tana, you can also pass existing Tana node data to these APIs and then receive results in return. The results of these calls can be added as new Tana nodes or can be used as input to further features like the built-in AI integration.
      </Typography>
      <Typography variant='body1' align='left' gutterBottom>
        In my own daily use of Tana I have found myself wanting various enhancements to Tana - things that aren't built-in already. The <code>Make API request</code> command gives me the ability to call out to custom code. Importantly, that code doesn't have to run "on the internet" somewhere but can in fact run on my local laptop via the <code>Avoid Proxy</code> setting of <code>Make API request</code>.
      </Typography>
      <Typography variant='body1' align='left' gutterBottom>
        As a software engineer, this really opens things up for me. And so I built a small service called `Tana Helper` and started adding functions to it.</Typography>
      <Typography variant='body1' align='left' gutterBottom>
        Full documentation and demonstrations of features can be found at <Link to="https://tana.pub/EufhKV4ZMH/tana-helper">Tana Helper</Link> (Tana pub site). The source code is open source under the MIT License and is available on github at <a href="https://www.github.com/verveguy/tana-helper">verveguy/tana-helper</a>.
      </Typography>
      <Typography variant='h4' align='left' gutterBottom>
        About this web UI
      </Typography>
      <Typography variant='body1' align='left' gutterBottom>
        Tana Helper is mostly used 'behind the scenes' while working in your Tana workspace. This is done via Tana Commands, in particular, the Make API Command. This UI provides access to a few features of Tana Helper that are outside the strict confines of the Tana workspace itself - the Visualizer and Tag Diagram tools. It also provides API documentation for each of the calls that Tana can make via Make API Request commands as well as access to the helper service logs if you have problems or want to know more about what is going on.
      </Typography>
    </div>
  );
}
