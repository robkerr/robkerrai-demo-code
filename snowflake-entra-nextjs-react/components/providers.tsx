// app/providers.tsx
'use client';

import { useEffect } from 'react';
import { AppInsightsContext } from '@microsoft/applicationinsights-react-js';
import { ApplicationInsights } from '@microsoft/applicationinsights-web';
import { ReactPlugin } from '@microsoft/applicationinsights-react-js';
import { MSALProviderWrapper } from '@/components/msal-provider';

const instrumentationKey = '1175f495-9868-4e8e-92a4-a157c8750a11'
const reactPlugin = new ReactPlugin();
const appInsights = new ApplicationInsights({
  config: {
    // connectionString: process.env.NEXT_PUBLIC_APPINSIGHTS_CONNECTION_STRING ?? 'InstrumentationKey=1175f495-9868-4e8e-92a4-a157c8750a11;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=3ab0bdc3-8dd3-400a-8869-acb7d5daf15b',
    instrumentationKey: instrumentationKey,
    enableAutoRouteTracking: true,
    extensions: [reactPlugin],
  },
});

export default function Providers({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // only initialize in the browser
    appInsights.loadAppInsights();
  }, []);

  return (
    <MSALProviderWrapper>
      <AppInsightsContext.Provider value={reactPlugin}>
        {children}
      </AppInsightsContext.Provider>
    </MSALProviderWrapper>
  );
}
