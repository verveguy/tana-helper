import React, { useContext, useEffect, useState } from "react";
import './Configure.css';
import { CircularProgress, Typography } from "@mui/material";
import axios from "axios";
import { TanaHelperContext } from "../TanaHelperContext";
import validator from '@rjsf/validator-ajv8';
import Form from '@rjsf/mui';
import { RJSFSchema } from '@rjsf/utils';


export default function Configure() {
  const { config, setConfig } = useContext(TanaHelperContext)
  const [schema, setSchema] = useState<RJSFSchema>({})

  useEffect(() => {
    (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'scroll');

    return () => {
      (document.querySelector('#root') as HTMLElement)?.style.setProperty('overflow', 'hidden');
    }

  }, []);

  useEffect(() => {
    axios.get('/configuration')
      .then(response => {
        console.log('Fetched config: ', response.data);
        setConfig(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  // fetch the schema we need from our generated openapi.json
  useEffect(() => {
    axios.get('/openapi.json')
      .then(response => {
        if (response.data != null) {
          const newSchema: RJSFSchema = response.data.components.schemas as RJSFSchema;
          console.log('Fetched schema: ');
          setSchema(newSchema['Settings']);
        }
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleChange = (data: any) => {
    console.log('Changed data: ', data);
  };

  const handleSubmit = (data: any) => {
    const newConfig = data.formData;
    setConfig(newConfig);
    if (newConfig != undefined) {
      axios.post('/configuration', newConfig)
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

  if (!config || !schema) {
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
          Configuration
        </Typography>
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