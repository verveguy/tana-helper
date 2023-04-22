/*

    Simple API service that retrieves your Calendar via
    the Apple Calendar app API.

    Allows iCloud, Google and Outlook calendars to be accessed
    since Apple Calendar syncs with all three of those systems.

    POST ./calendar accepts a JSON payload of params and returns
    the calender entries in Tana paste format.

    Uses osascript and swift code underneath invoked via exec()

    See the getcalendar.swift script for parameter information

    {
        me: "self name",
        one2one: true | false,
        meeting: "#tag",
        person: "#tag",
        solo: true | false,
        calendar: "Calendar to read from",
        offset: -n | 0 | +n
        range: >= 1 - how many days
    }
*/

import { Request, Response } from "express";
import { exec } from 'child_process';
import { app } from "./server.js";

function makeCmdSwitch(cmdSwitch: string, value: string) {
  return value == null ? "" : `${cmdSwitch} '${value}'`;
}

function paramsFromPayload(req: Request) {
  // debug log
  console.log(req.body);
  const me = makeCmdSwitch("-me", req.body.me);
  const calendar = makeCmdSwitch("-calendar", req.body.calendar);
  const solo = req.body.solo ? "-solo" : "";
  const one2one = makeCmdSwitch("-one2one", req.body.one2one);
  const meeting = makeCmdSwitch("-meeting", req.body.meeting);
  const person = makeCmdSwitch("-person", req.body.person);
  const offset = makeCmdSwitch("-offset", req.body.offset);
  const range = makeCmdSwitch("-range", req.body.range);

  let ignores:string = (req.body.ignore ?? []).reduce((result:string, x:string) => makeCmdSwitch("-ignore", x), "");
  return { me, calendar, solo, one2one, meeting, person, offset, range, ignores};
}

app.post('/calendar', async (req: Request, res: Response) => {

  // TODO: extract params from JSON
  const { me, calendar, solo, one2one, meeting, person, offset, range, ignores} = paramsFromPayload(req);

  // calendar_auth.scpt is important to ensure authentication UI presented 
  // to the user on the first time they run this service invocation
  let cmdLine = "osascript ./src/calendar_auth.scpt >/dev/null && ./src/getcalendar.swift -noheader";
  cmdLine += ` ${me} ${calendar} ${solo} ${one2one} ${meeting} ${person} ${offset} ${range} ${ignores}`;

  console.log("Cmd line: " + cmdLine);

  await exec(cmdLine, (error, stdout, stderr) => {
    if (error) {
      res.status(200).send(stderr);
      return;
    }
    if (stderr) {
      res.status(200).send(stderr);
      return;
    }
    console.log(stdout);
    res.status(200).send(stdout);
  });

});
