
"use client";
import React, { useState, useRef, useEffect } from "react";
import dynamic from "next/dynamic";
import type { RowData, SnowflakeResponse } from "@/lib/types";
import { useToast } from "@/components/ui/use-toast";
import { appInsights } from '@/components/appInsights';

// Dynamically import the ScrollableDataTable component for client-side rendering only
const ScrollableDataTable = dynamic(() => import("@/components/scrollable-data-table"), { ssr: false });
import { useMsal } from "@azure/msal-react";
// import { BrowserUtils } from "@azure/msal-browser";
import { snowflakeQuery } from '@/lib/snowflake-query';
import { get_query } from '@/lib/api';
import { isUserLoggedIn, verifyLogin, signOut, getAccessToken, getUserDisplayName } from "@/lib/msal-helper";


export default function ChatPage() {
  // Query input from user
  // const [defaultQuery, setDefaultQuery] = useState<string>("TYPE QUERY HERE");
  const [input, setInput] = useState<string>("TYPE QUERY HERE");

  // Output column headings and data from Snowflake
  const [headings, setHeadings] = useState<string[]>([]);
  const [entries, setEntries] = useState<RowData[]>([]);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { toast } = useToast();
  
  //Get Reference to global MSAL instance
  const { instance } = useMsal();

  
  // const [tokenIssuance, setTokenIssuance] = useState(null);
  // const [tokenExpiration, setTokenExpiration] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [userDisplayName, setUserDisplayName] = useState<string | null>(null);

  async function fetchSampleQuery() {
    const accessToken = await getAccessToken(instance, process.env.NEXT_PUBLIC_SNOWFLAKE_SCOPE);

    if (!accessToken) {
      toast({
        title: "Entra Authentication Success",
        description: "No access token available."
      });
      return false;
    }

    try {
      const api_sql = await get_query(accessToken);
      setInput(api_sql);

      console.log("SQL Query to execute:", api_sql);
    } catch (error) {
      toast({
        title: "API Call Failed",
        description: `${error}`,
        variant: "destructive"
      });
      return false;
    }
  };

  async function submitQuery(sql: string): Promise<boolean> {
    const accessToken = await getAccessToken(instance, process.env.NEXT_PUBLIC_SNOWFLAKE_SCOPE);

    if (!accessToken) {
      toast({
        title: "Entra Authentication Success",
        description: "No access token available."
      });
      return false;
    }

    try {
      const response: SnowflakeResponse = await snowflakeQuery(sql, accessToken);

      if (!response.success) {
        toast({
          title: "Snowflake Query Failed",
          description: response.error ?? "No SQL response received.",
          variant: "destructive"
        });
        return false;
      } else {
        setEntries(response.data ?? []);
        setHeadings(response.headings ?? []);
        return true;
      }
    } catch (error) {
      toast({
        title: "Snowflake Query Failed",
        description: `Error executing SQL query: ${error}`,
        variant: "destructive"
      });
      return false;
    }
  }

  async function loginOrGetUserInfo() {
    appInsights.trackEvent({ name: 'Logging in' });
    // Verify login, display login popup if needed
    const verifyResult = await verifyLogin(instance, process.env.NEXT_PUBLIC_SNOWFLAKE_SCOPE);

    if (!verifyResult.success) {
      console.log("Login verification failed:", verifyResult.message);
      setIsLoggedIn(false);
      setUserDisplayName(null); // Clear display name on failure
      toast({
        title: "Entra Authentication Error",
        description: verifyResult.message,
        variant: "destructive",
      });
    } else {
      setIsLoggedIn(true);
      setUserDisplayName(verifyResult.displayName);
      appInsights.setAuthenticatedUserContext(verifyResult.displayName);
      toast({
        title: "Entra Authentication Success",
        description: verifyResult.message
      });
    }
  };

  async function logout() {
    appInsights.trackEvent({ name: 'Logging Out' });
    console.log("logging out");
    const success = await signOut(instance);
    if (success) {
      console.log("User logged out successfully.");
      setIsLoggedIn(false);
      setUserDisplayName(null);
      toast({
        title: "Entra Logout Success",
        description: "You have been logged out successfully.",
      });
    } else {
      console.error("Logout failed.");
      toast({
        title: "Entra Logout Error",
        description: "Failed to log out. Please try again.",
        variant: "destructive",
      });
    }
    // Add actual logout logic here if needed
  }

  useEffect(() => {
    const checkLogin = async () => {
      // Configuation check
      if (!instance) {
        const errorMessage = "MSAL instance is not available in useEffect.";
        console.error(errorMessage);
        setUserDisplayName(null); // Clear display name on failure
        toast({
          title: "Entra Configuration Error",
          description: "MSAL instance is not available. Please check your configuration.",
          variant: "destructive",
        });
      }

      const loggedIn = await isUserLoggedIn(instance);
      setIsLoggedIn(loggedIn);

      if (loggedIn) {
        // If already logged in, get user display name
        const displayName = await getUserDisplayName(instance);
        setUserDisplayName(displayName);
        toast({
          title: "Entra Authentication Success",
          description: `Welcome back, ${displayName ?? "User"}!`,
        });
      } else {
        // Since we can't get the display name, force a login flow
        setIsLoggedIn(false);
        setUserDisplayName(null);
      }
    }

    checkLogin();
  }, [instance, toast]);

  


  function handleInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() !== "") {
        handleGo();
      }
    }

  }

  async function handleGetSampleQuery() {
    await fetchSampleQuery();
  }
    

  async function handleGo() {
    if (input.trim() === "") return;

    const success = await submitQuery(input);
    
    if (!success) {
      // If the query failed, we can show an error message or reset the input
      console.log("Query execution failed.");
      setHeadings([]); // Clear headings on error
      setEntries([]); // Clear entries on error
      return;
    } 

    if (textareaRef.current) textareaRef.current.focus();
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a66c2] via-[#004182] to-[#002447]">
        <div className="absolute top-20 left-20 w-72 h-72 bg-white/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-40 right-32 w-96 h-96 bg-[#0077b5]/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute bottom-32 left-1/3 w-80 h-80 bg-white/5 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Header Bar */}
      <header className="relative z-20 w-full flex items-center justify-between px-8 py-4 bg-white/10 backdrop-blur-xl border-b border-white/20 shadow-lg">
        <div className="flex items-center">
          <span className="text-2xl font-bold text-white tracking-tight">Snowflake OAuth Integration Test</span>
        </div>
        <div className="flex items-center gap-4">
          {isLoggedIn && userDisplayName && (
            <>
              <span className="text-white/90 font-medium text-lg truncate max-w-[200px]">{userDisplayName}</span>
              <button
                onClick={logout}
                className="ml-2 px-3 py-1 rounded-lg bg-gradient-to-r from-[#3b82f6] to-[#1e40af] text-white text-sm font-semibold shadow border-0 transition-all duration-200 hover:from-[#2563eb] hover:to-[#1e3a8a]"
                style={{ minWidth: 0 }}
              >
                Logout
              </button>
            </>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-[80vw]" style={{ minWidth: 0 }}>
          <div className="text-center mb-8">
            <p className="text-white/80 text-lg font-medium">
              This test scaffold allows you to execute SQL queries against a Snowflake database <br />using your Entra ID and OAuth access token authentication.
            </p>
          </div>

          {/* Glassmorphic Card or Sign-in Prompt */}
          {isLoggedIn ? (
            <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl shadow-2xl overflow-hidden">
              {/* Card Header */}
              <div className="bg-gradient-to-r from-white/20 to-white/10 backdrop-blur-sm p-8 border-b border-white/20">
                <h2 className="text-2xl font-semibold text-white text-center">
                  Send SQL Statement to Snowflake
                </h2>
                <p className="text-white/70 text-center mt-2">
                  Enter a query against the SHIP_PLAN table to test OAuth.
                </p>
              </div>

              {/* Card Content */}
              <div className="p-8 space-y-6">
                <div className="flex gap-3 items-end">
                  <textarea
                    ref={textareaRef}
                    rows={3}
                    value={input}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    placeholder="Type your message..."
                    className="flex-1 resize-vertical p-3 rounded-2xl bg-white/20 text-white placeholder-white/60 font-medium text-lg border border-white/20 focus:outline-none focus:ring-2 focus:ring-[#0a66c2] backdrop-blur-md shadow-inner min-h-[60px]"
                    style={{ minHeight: 60 }}
                  />
                  
                  <button
                    onClick={handleGetSampleQuery}
                    disabled={input.trim() === ""}
                    className="h-12 min-w-[60px] px-6 rounded-2xl bg-gradient-to-r from-white to-white/90 text-[#0a66c2] font-semibold text-lg shadow-xl border-0 transition-all duration-300 transform hover:scale-[1.04] hover:from-white/90 hover:to-white/80 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    Get Query
                  </button>

                  <button
                    onClick={handleGo}
                    disabled={input.trim() === ""}
                    className="h-12 min-w-[60px] px-6 rounded-2xl bg-gradient-to-r from-white to-white/90 text-[#0a66c2] font-semibold text-lg shadow-xl border-0 transition-all duration-300 transform hover:scale-[1.04] hover:from-white/90 hover:to-white/80 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  >
                    Go
                  </button>
                </div>

                {entries.length > 0 && (
                  <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-5 mt-6 overflow-x-auto">
                    <ScrollableDataTable headings={headings} data={entries} />
                  </div>
                )}
              </div>

            </div>
          ) : (
            <div className="mx-auto bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl shadow-2xl overflow-hidden flex flex-col items-center justify-center p-12 max-w-xs" style={{ maxWidth: 400 }}>
              <h2 className="text-2xl font-semibold text-white text-center mb-6">
                Sign in to Entra ID
              </h2>
              <button
                onClick={loginOrGetUserInfo}
                className="w-full max-w-xs h-16 bg-gradient-to-r from-[#3b82f6] to-[#1e40af] text-white font-semibold text-lg shadow-xl border-0 rounded-2xl transition-all duration-300 transform hover:scale-[1.04] hover:from-[#2563eb] hover:to-[#1e3a8a] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                Sign In
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
