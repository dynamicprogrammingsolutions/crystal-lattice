# Shared theme contract

The shared React Native `Theme` separates foregrounds by the surface they are
drawn on.

- `text` is ordinary content on application backgrounds and surfaces.
- `textOnPrimary` is content on a solid `primary` control such as a filled
  button.
- `bubbleUserText` is content drawn directly on `bubbleUserBg`.

Do not use `textOnPrimary` for a translucent user bubble. In the light theme,
`bubbleUserBg` is a low-opacity blue over a light background, so white text
does not provide sufficient contrast. The maintained static themes use:

- light: dark `bubbleUserText` on translucent light blue;
- dark: light `bubbleUserText` on dark blue.

Platform theme builders may derive `bubbleUserText` from the effective
composited bubble background. User-message prose, headings, lists, links,
inline code, raw text, headers, and footers should use this token when they
are rendered directly on the bubble. Attachment tiles, buttons, and other
controls with their own opaque backgrounds continue to use the foreground
token for their own surface.