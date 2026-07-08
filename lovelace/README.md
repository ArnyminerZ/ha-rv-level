# Dashboard cards

These are **not** part of the HACS integration install — HACS integration
repositories can't ship Lovelace resources automatically. They're plain
dashboard YAML you paste in yourself, meant as a working starting point you
then tweak to taste.

## Files

- **`bubble-card.yaml`** — a circular bubble-level indicator that moves with
  pitch/roll and turns green/red depending on whether the vehicle is level.
- **`chock-display-card.yaml`** — a picture-elements card overlaid on a
  top-view image of your vehicle, showing how many wheels need a chock, how
  tall a chock, and whether the vehicle is level / levelable at all.

## Prerequisites

Both cards use community custom cards, installed as **Frontend** repositories
in HACS:

- [`html-card`](https://github.com/pkozul/ha-html-card) — used by
  `bubble-card.yaml`.
- [`lovelace-mushroom`](https://github.com/piitaya/lovelace-mushroom) — used
  by `chock-display-card.yaml`.

## How to use

1. Install the RV Level integration and complete its config flow first — the
   cards reference the entities it creates.
2. Install the custom cards above via HACS -> Frontend, then reload your
   browser.
3. Open the dashboard you want to add the card to, switch to YAML mode for a
   view/card, and paste the contents of the file you want.
4. **Replace `rv_level` in every entity ID** with your own device's slug, if
   you renamed the "RV Level" device during setup. You can check the actual
   entity IDs under Settings -> Devices & services -> RV Level -> the device
   page lists every entity.
5. For `chock-display-card.yaml`, replace `image: /local/your-vehicle-top-view.png`
   with a top-view picture of your own vehicle placed in
   `config/www/your-vehicle-top-view.png` (served at `/local/...`).

## Notes / known limitations

- The chock icons (`mdi:chevron-up` / `-double-up` / `-triple-up`) reflect
  the chock's *index* within your configured preset (1st, 2nd, 3rd step), not
  an absolute height, since chock presets can have any number of steps at any
  height. If your preset only has 1 or 2 steps, `chock_index` will simply
  never reach 3.
- `bubble-card.yaml` deliberately uses the same pixels-per-degree scale for
  the moving bubble and the dashed "level zone" circle, so the zone boundary
  is exactly where the vehicle stops being level. (The original hand-written
  template this was adapted from used two different scales for those, which
  made the zone look bigger than it actually was — fixed here.)
