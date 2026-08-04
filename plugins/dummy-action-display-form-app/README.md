# dummy-action-display-form-app

Demo application plugin for manually testing generic action display embedded
forms.

It contributes a session action that returns a display with:

- markdown/plain text instructions
- a multiline callback URL field
- a note field
- a select field
- Submit and Cancel follow-up actions

Submit maps values through `$form.<field>` and returns a confirmation display.
Cancel uses the generic `dismiss` action and should close the display without a
backend call.

Example config entry:

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/dummy-action-display-form-app"
  ]
}
```

Equivalent explicit entry form:

```json
{
  "plugins": [
    {
      "path": "${env:BUILTIN_PLUGINS}/dummy-action-display-form-app",
      "entry": "dummy_action_display_form_app.DummyActionDisplayFormAppPlugin"
    }
  ]
}
```

Manual flow:

1. Start the terminal HTTP backend with this plugin enabled.
2. Open a session from the mobile or desktop app.
3. Run the `Show display form` session action.
4. Enter a callback URL and note.
5. Choose a mode if the frontend renders select controls.
6. Press `Submit`.
7. Verify the confirmation display echoes the safe values you entered.
8. Run the action again and press `Cancel`; the display should close without an
   action error.