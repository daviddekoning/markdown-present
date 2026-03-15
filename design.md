# Markdown Present

## Functional Requirements

This app will take presentations formatted in markdown and present them in the browser. The presenter will upload a zipped markdown files (with any referenced assets).

The presenter will get a presenter view. This view will
- allow them to naviagate forwards and backwards through the deck
- when the presenter presses 'g', it will show them all the slides and let them jump to one by clicking
- show a url that the presenter can share with others.
- a dark and light mode switch
- an 'End Presentation' button.

The audience view, accessible from the url above, is only available during the presentation (between upload and 'End Presentation').
- When a user goes to that url, they will see the current slide that the presenter is viewing
- when the presenter changes slide (via any mechanism), the audience view will update
- there will be a dark / light mode option for each audience member.

Key modes:
- upload: the UI for letting the user upload a deck and initiate a presentation
- present: when the presentation is live
- post-presentation: after the presentation

## Tech stack

Use fastAPI to write the server. Use a pure HTML frontend (no React).

Delete presenations from the server after a presentation is complete. There is no requirement for any persistence on the server.

Store all user data (dark/light mode selection, 3 last presentations (the zip files)) in the browser storage.

Deploy to fly.io. No attached volumes or S3 buckets - purely stateless.