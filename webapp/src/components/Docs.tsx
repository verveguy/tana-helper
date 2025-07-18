import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

export default function Docs() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Documentation</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">Documentation content will be available here.</p>
      </CardContent>
    </Card>
  );
}
