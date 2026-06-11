# Local Notifications And Background Refresh

This document explains the local-only or direct-IP-friendly concepts behind Stage 1 of the plan, especially what can happen without APNs/FCM and what the platform limits are.

## Local notification versus remote push

### Local notification

A local notification is scheduled or triggered by the app on the device itself.

Examples:

- remind me in 30 minutes
- show a notice after the app finished a local refresh
- show a notification after the app polls the server and discovers a new event

### Remote push

A remote push notification is sent by an external backend to APNs/FCM, which then asks the OS to deliver it.

## What “background” means

An app is not always free to run network code whenever it wants.

### iOS

iOS commonly suspends apps in the background. The system may wake the app for specific kinds of work, but the app should not assume it can maintain arbitrary polling or WebSocket connectivity forever.

### Android

Android is more flexible than iOS but still applies battery and background-execution restrictions. Periodic work is allowed, but exact timing is not guaranteed. Long-running background behavior generally requires a foreground service.

## Two polling modes in the staged plan

### Active polling

Use this when the app is actively connected:

- app is foregrounded
- or bridge client is polling the local server on the laptop

Expected cadence:

- about every 5-15 seconds at first

This can later evolve into long-poll or NDJSON streaming.

### Periodic wake-up polling

Use this when the app is in background and OS schedulers may wake it only occasionally.

Expected cadence:

- about every 5 minutes for the first version

This is not meant to be instant. It is a best-effort refresh path for users who want direct-IP mode without outside push services.

## iOS concepts

### BGAppRefreshTask

`BGAppRefreshTask` is an iOS background task mechanism that lets the app request periodic refresh opportunities.

Important limitation:

- the system decides when the refresh actually runs
- it is not guaranteed at exact times

### Background Fetch / background execution

Older iOS background-fetch concepts have the same general limitation: the OS decides when to wake the app.

### Local notifications on iOS

If the app successfully wakes, refreshes, and sees a new notification record, it can schedule or present a local notification. But the app first has to get the runtime opportunity.

## Android concepts

### WorkManager

`WorkManager` is Android’s recommended API for deferrable background work. It is suitable for periodic refresh jobs but is intentionally inexact.

### Foreground service

A foreground service is an Android service the user can see because the system shows an ongoing notification for it. This is the Android-friendly path if the product ever wants more continuous direct-IP background listening.

### Local notifications on Android

When background work runs and detects new notification records, the app can post local notifications.

## What direct-IP users can realistically expect

### Foreground app

Direct-IP works well here:

- phone can poll the laptop/server directly
- short polling intervals are okay
- local notification or in-app banner can appear quickly

### Background app

Direct-IP is best-effort only:

- iOS may wake the app occasionally
- Android periodic work is also not exact
- notifications may be delayed

### Terminated app

Without APNs/FCM, the app will not get arbitrary instant wakeups for unpredictable external events.

## Why Stage 1 still matters

Even with these limitations, the local polling stage is valuable because it:

- supports direct-IP-only users
- supports self-hosters who do not want any outside push service
- defines the notification data model early
- gives foreground users useful notifications immediately
- creates the API shape later reused by bridge push delivery

## Terms used by the plan

### Cursor

A cursor is the “where did I stop last time?” marker used by polling endpoints. `/events` already uses this kind of idea, and `/notifications` should do the same.

### Long poll

A long-poll endpoint keeps an HTTP request open for a while until new data arrives or a timeout happens. It reduces needless repeated requests while preserving a simple HTTP shape.

### NDJSON

NDJSON means newline-delimited JSON. It is a streaming format where each line is a JSON object. It can be useful later if notification streaming grows beyond simple polling.

## What the staged plan assumes here

- Stage 1 uses local polling first.
- Foreground polling can be fast.
- Background scheduler polling can be slow.
- No external push provider is required to complete Stage 1.
