import React, { useContext, useEffect, useState } from "react";
import './Webhooks.css';
import { CircularProgress, List, Typography } from "@mui/material";
import axios from "axios";
import { TanaHelperContext } from "../TanaHelperContext";
import validator from '@rjsf/validator-ajv8';
import Form from '@rjsf/mui';
import { RJSFSchema } from '@rjsf/utils';


export default function Webhooks() {
  const { webhooks, setWebhooks } = useContext(TanaHelperContext)
  // const [schema, setSchema] = useState<RJSFSchema>({})

  useEffect(() => {
    (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'scroll');

    return () => {
      (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'hidden');
    }

  }, []);

  useEffect(() => {
    axios.get('/webhooks')
      .then(response => {
        console.log('Fetched webhooks: ', response.data);
        setWebhooks(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  // fetch the schema we need from our generated openapi.json
  // useEffect(() => {
  //   axios.get('/openapi.json')
  //     .then(response => {
  //       if (response.data != null) {
  //         const newSchema: RJSFSchema = response.data.components.schemas as RJSFSchema;
  //         console.log('Fetched schema: ');
  //         setSchema(newSchema['Settings']);
  //       }
  //     })
  //     .catch(error => {
  //       console.error(error);
  //     });
  // }, []);

  const handleChange = (data: any) => {
    console.log('Changed data: ', data);
  };

  const handleSubmit = (data: any) => {
    const newWebhooks = data.formData;
    setWebhooks(newWebhooks);
    if (newWebhooks != undefined) {
      axios.post('/webhooks', newWebhooks)
        .then(response => {
          console.log('Response: ', response);
        })
        .catch(error => {
          console.error(error);
        });
    }
  };

  const onError = (data: any) => {
    console.log('Data: ', data);
  };

  if (!webhooks) {
    return (
      <div className="config-container">
        <div className="spinner-container">
          <div className="spinner">
            <CircularProgress />
          </div>
        </div>
      </div>
    );
  }
  else {
    return (
      <div className='config-container'>
        <Typography variant='h4' align='left' gutterBottom>
          Webhooks
        </Typography>
        <List>
          { webhooks.map((item: any) => {
            return (
              <div key={item.id}>
                <Typography variant='h6' align='left' gutterBottom>
                  {item.name}
                </Typography>
                <Typography variant='body1' align='left' gutterBottom>
                  {item.url}
                </Typography>
              </div>
            );
          
          }
        </List>
        <Form
          schema={schema}
          formData={config}
          validator={validator}
          onChange={handleChange}
          onSubmit={handleSubmit}
          onError={onError}
        />
      </div>
    );
  }
}