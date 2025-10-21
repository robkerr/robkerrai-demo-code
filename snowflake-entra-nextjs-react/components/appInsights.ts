'use client';
// src/appInsights.ts
import { ApplicationInsights } from '@microsoft/applicationinsights-web';
import { ReactPlugin } from '@microsoft/applicationinsights-react-js';

const reactPlugin = new ReactPlugin();
const instrumentationKey = '1175f495-9868-4e8e-92a4-a157c8750a11'
// import { Toaster } from "@/components/ui/toaster";

// enableDebug and loggingLevelConsole can be disabled when pushed to production
const appInsights = new ApplicationInsights({
  config: {
    instrumentationKey: instrumentationKey,
    enableDebug: true,
    loggingLevelConsole: 0,
    extensions: [reactPlugin]
  }
});


appInsights.addTelemetryInitializer((envelope) => {
  envelope.tags = envelope.tags || {};
  envelope.tags["ai.cloud.role"] = "KLA-NextJS-Test-App";
});


appInsights.loadAppInsights();

export { appInsights, reactPlugin };
