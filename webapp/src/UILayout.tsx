import React, { ReactNode, useState } from "react";
import { Routes } from "react-router-dom";
import { Menu, X, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "./components/ui/button";
import { cn } from "./lib/utils";

const SIDEBAR_WIDTH = 240;

interface UILayoutProps {
  menuItems?: ReactNode[];
  routes?: ReactNode[];
  content?: ReactNode;
  control?: ReactNode;
}

export default function UILayout({ menuItems, routes, content, control }: UILayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  // If we have routes, render the full layout
  if (routes) {
    return (
      <div className="flex h-screen bg-background">
        {/* Sidebar */}
        <div
          className={cn(
            "relative flex flex-col bg-card border-r border-border transition-all duration-300 ease-in-out",
            sidebarOpen ? "w-60" : "w-16"
          )}
        >
          {/* Sidebar Header */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            {sidebarOpen && (
              <h1 className="text-xl font-semibold text-foreground">
                Tana Helper
              </h1>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="ml-auto"
            >
              {sidebarOpen ? (
                <ChevronLeft className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Navigation */}
          {sidebarOpen && menuItems && (
            <nav className="flex-1 p-4">
              <div className="space-y-2">
                {menuItems}
              </div>
            </nav>
          )}

          {/* Controls Section */}
          {sidebarOpen && control && (
            <div className="border-t border-border p-4">
              <div className="text-sm font-medium text-muted-foreground mb-2">
                Controls
              </div>
              {control}
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top bar for collapsed sidebar */}
          {!sidebarOpen && (
            <div className="flex items-center p-4 border-b border-border bg-card">
              <Button variant="ghost" size="icon" onClick={toggleSidebar}>
                <Menu className="h-4 w-4" />
              </Button>
              <h1 className="ml-4 text-xl font-semibold text-foreground">
                Tana Helper
              </h1>
            </div>
          )}

          {/* Content Area */}
          <main className="flex-1 overflow-auto p-6">
            <Routes>
              {routes}
            </Routes>
          </main>
        </div>
      </div>
    );
  }

  // If we have individual content/control, render the simplified layout
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Control Panel */}
          {control && (
            <div className="lg:col-span-1">
              <div className="sticky top-6">
                <div className="bg-card border border-border rounded-lg p-4">
                  <h2 className="text-lg font-semibold mb-4 text-foreground">
                    Controls
                  </h2>
                  {control}
                </div>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className={cn(
            "w-full",
            control ? "lg:col-span-3" : "lg:col-span-4"
          )}>
            {content}
          </div>
        </div>
      </div>
    </div>
  );
}
