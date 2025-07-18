import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

export default function Webhooks() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Webhooks</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">Webhook configuration will be available here.</p>
      </CardContent>
    </Card>
  );
}