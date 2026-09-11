# Grove & Stone: animated fruit hero

The hero now uses an original, silent 10-second mixed-fruit video instead of the plain background and separate framed photograph. It includes mango, kiwi, dragon fruit, strawberry and citrus, with a golden backdrop. The supplied iStock clip was viewed only as a motion/style reference; none of its frames are included in the project.

## How it works

- `mobile/src/FruitVideo.tsx` uses Expo Video for the same MP4 on Android and web. The video loops, is muted and plays inline. A JPEG poster covers loading and playback errors.
- `mobile/src/Hero.tsx` keeps offers, slide buttons, collection links and the mango shortcut. The pause button controls both slides and video. Reduced-motion preferences, app backgrounding and tab focus stop playback. The phone crop favours the fruit area; the text sits on a translucent cream panel.
- `mobile/assets/hero/grove-and-stone-fruit-loop.mp4` is the finished H.264 video: 1280 x 720, 24 fps, 10 seconds, approximately 1.4 MB. There is no audio track or watermark.
- `infra/media/render-fruit-loop.py` reproduces the video from the original transparent cutout sheet. Install `pillow` and `imageio-ffmpeg` only when rebuilding this artwork; the deployed app does not need them.

The built-in image-generation tool created the original fruit sheet. Final prompt: "Create a photorealistic fruit cutout sprite sheet for an original Grove & Stone fruit-shop animated advertisement. Transparent background with actual alpha. Wide 1536x1024 layout, exactly 6 separate isolated objects arranged in a strict 3-column x 2-row grid, one object centered in each cell, generous transparent margins, no overlaps. Top row: golden ripe mango cheek with scored juicy cubes; vibrant green kiwi circular cross section; magenta dragonfruit half with white flesh and tiny black seeds. Bottom row: juicy orange circular slice; red strawberry with little green crown; pink grapefruit circular slice. All photographed from slightly varied near-top angles with exquisite realistic wet flesh textures and bright warm studio lighting. Each object completely within its own cell, no cast shadows outside fruit, no plates, no text, no lettering, no logo, no watermark. These six isolated fruit pieces will be individually animated drifting and tumbling against a golden background."

Animation was composed programmatically with Pillow and encoded with FFmpeg. This is an original motion composition from generated still artwork, not a filmed or generatively simulated 3D video.

## Render failure and fix

The initial Render service tried `gunicorn app:app`, but this project exposes its application in `wsgi.py`. The service now initializes the schema and starts `gunicorn wsgi:app`. The missing production environment settings were configured privately, including the signing secret and database connection. `/api/v1/health` is the health check, and CORS permits the deployed website.

The free API can sleep while idle. Startup now waits up to 90 seconds for its health endpoint before requesting the catalog, so the previous 15-second ordinary request timeout does not immediately fail the first visit. An unavailable service still produces a retry button. No automatic retries of purchases or other writes were added.

Website: https://grove-and-stone-web.onrender.com

API health: https://grove-and-stone.onrender.com/api/v1/health

The private repository excludes `.env`, `.env.*` and `node_modules/`; only placeholder `.env.example` files are tracked. Dependencies still install during setup/build. The Android source is exportable, but a signed APK and physical-device playback remain separate checks.
