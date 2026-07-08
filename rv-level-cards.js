/**
 * RV Level dashboard cards.
 *
 * Two dependency-free custom cards for the RV Level integration:
 *   - <rv-level-bubble-card>  a circular bubble-level indicator
 *   - <rv-level-vehicle-card> a top-down per-wheel chock/lift overview
 *
 * Deliberately written with no build step and no external libraries: each
 * card is a plain custom element with a shadow root, updated by mutating
 * already-built DOM nodes rather than re-rendering a template string every
 * time `hass` changes. Home Assistant's own `<ha-card>` and `<ha-icon>`
 * elements are used directly -- they are registered globally by the HA
 * frontend, so any custom element's shadow root can use them without
 * importing anything.
 */

// ---------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------

function rvlIconForChockIndex(index) {
  if (index >= 3) return "mdi:chevron-triple-up";
  if (index === 2) return "mdi:chevron-double-up";
  if (index === 1) return "mdi:chevron-up";
  return "mdi:circle-outline";
}

function rvlFormatCm(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `${n.toFixed(1)} cm` : "?";
}

// ---------------------------------------------------------------------
// <rv-level-bubble-card>
// ---------------------------------------------------------------------

class RvLevelBubbleCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._built = false;
  }

  setConfig(config) {
    if (!config.bubble_entity) {
      throw new Error(
        "rv-level-bubble-card: 'bubble_entity' is required (e.g. sensor.rv_level_bubble_position)"
      );
    }
    this._config = { title: "Level", size: 220, ...config };
    this._built = false;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return {
      title: "Level",
      bubble_entity: "sensor.rv_level_bubble_position",
      level_entity: "binary_sensor.rv_level_level",
    };
  }

  _build() {
    const size = this._config.size;
    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .rvl-title {
          font-size: 1rem;
          font-weight: 500;
          color: var(--primary-text-color);
          margin-bottom: 8px;
        }
        .rvl-circle {
          position: relative;
          width: ${size}px;
          height: ${size}px;
          max-width: 100%;
          margin: 8px auto;
          border-radius: 50%;
          background: radial-gradient(circle, var(--card-background-color) 55%, var(--divider-color) 170%);
          border: 2px solid var(--divider-color);
          box-sizing: border-box;
        }
        .rvl-axis-v, .rvl-axis-h {
          position: absolute;
          background: var(--divider-color);
        }
        .rvl-axis-v { left: 50%; top: 7%; bottom: 7%; width: 1px; }
        .rvl-axis-h { top: 50%; left: 7%; right: 7%; height: 1px; }
        .rvl-zone {
          position: absolute;
          left: 50%;
          top: 50%;
          transform: translate(-50%, -50%);
          border: 1.5px dashed var(--success-color, #2ecc71);
          border-radius: 50%;
          box-sizing: border-box;
        }
        .rvl-bubble {
          position: absolute;
          width: 13%;
          height: 13%;
          border-radius: 50%;
          border: 1.5px solid var(--primary-text-color);
          opacity: 0.85;
          transition: left 0.2s ease, top 0.2s ease, background-color 0.2s ease;
          box-sizing: border-box;
        }
        .rvl-missing {
          color: var(--error-color, #e74c3c);
          padding: 8px 0;
        }
      </style>
      <ha-card>
        <div class="rvl-title"></div>
        <div class="rvl-circle">
          <div class="rvl-axis-v"></div>
          <div class="rvl-axis-h"></div>
          <div class="rvl-zone"></div>
          <div class="rvl-bubble"></div>
        </div>
        <div class="rvl-missing" hidden></div>
      </ha-card>
    `;
    this._titleEl = this.shadowRoot.querySelector(".rvl-title");
    this._zoneEl = this.shadowRoot.querySelector(".rvl-zone");
    this._bubbleEl = this.shadowRoot.querySelector(".rvl-bubble");
    this._missingEl = this.shadowRoot.querySelector(".rvl-missing");
    this._circleEl = this.shadowRoot.querySelector(".rvl-circle");
    this._built = true;
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._built) this._build();

    this._titleEl.textContent = this._config.title || "";

    const bubbleState = this._hass.states[this._config.bubble_entity];
    if (!bubbleState) {
      this._circleEl.hidden = true;
      this._missingEl.hidden = false;
      this._missingEl.textContent = `Entity not found: ${this._config.bubble_entity}`;
      return;
    }
    this._circleEl.hidden = false;
    this._missingEl.hidden = true;

    const attrs = bubbleState.attributes;
    const x = Number(attrs.x ?? 0);
    const y = Number(attrs.y ?? 0);
    const pitchMargin = Number(attrs.pitch_margin ?? 1.5);
    const rollMargin = Number(attrs.roll_margin ?? 1.5);
    const maxAngle = Number(attrs.bubble_max_angle ?? 6) || 6;

    const isLevel = this._config.level_entity
      ? this._hass.states[this._config.level_entity]?.state === "on"
      : Math.abs(x) * maxAngle <= rollMargin && Math.abs(y) * maxAngle <= pitchMargin;

    // Half-width of the playing field, as a percentage of the circle, so the
    // dashed "level zone" and the bubble itself share the exact same scale
    // (crossing out of the dashed circle is exactly when isLevel flips).
    const halfFieldPct = 43; // circle radius minus a small margin for the bubble itself
    const clampedX = Math.max(-1, Math.min(1, x));
    const clampedY = Math.max(-1, Math.min(1, y));

    this._bubbleEl.style.left = `${50 + clampedX * halfFieldPct - 6.5}%`;
    this._bubbleEl.style.top = `${50 + clampedY * halfFieldPct - 6.5}%`;
    this._bubbleEl.style.backgroundColor = isLevel
      ? "var(--success-color, #2ecc71)"
      : "var(--error-color, #e74c3c)";

    this._zoneEl.style.width = `${((rollMargin / maxAngle) * halfFieldPct * 2).toFixed(2)}%`;
    this._zoneEl.style.height = `${((pitchMargin / maxAngle) * halfFieldPct * 2).toFixed(2)}%`;
  }
}

customElements.define("rv-level-bubble-card", RvLevelBubbleCard);

// ---------------------------------------------------------------------
// <rv-level-vehicle-card>
// ---------------------------------------------------------------------

const RVL_GENERIC_VAN_SVG = `
<svg viewBox="0 0 200 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
  <rect x="30" y="18" width="140" height="284" rx="26" fill="var(--card-background-color, #fff)" stroke="currentColor" stroke-width="3"/>
  <rect x="48" y="38" width="104" height="46" rx="10" fill="none" stroke="currentColor" stroke-width="2" opacity="0.6"/>
  <rect x="16" y="78" width="10" height="18" rx="4" fill="currentColor" opacity="0.5"/>
  <rect x="174" y="78" width="10" height="18" rx="4" fill="currentColor" opacity="0.5"/>
  <rect x="6" y="52" width="16" height="40" rx="6" fill="var(--disabled-text-color, #888)"/>
  <rect x="178" y="52" width="16" height="40" rx="6" fill="var(--disabled-text-color, #888)"/>
  <rect x="6" y="228" width="16" height="40" rx="6" fill="var(--disabled-text-color, #888)"/>
  <rect x="178" y="228" width="16" height="40" rx="6" fill="var(--disabled-text-color, #888)"/>
  <line x1="100" y1="100" x2="100" y2="290" stroke="currentColor" stroke-width="1" opacity="0.15"/>
</svg>
`;

const RVL_CORNERS = [
  { key: "front_left", top: 20, left: 16 },
  { key: "front_right", top: 20, left: 84 },
  { key: "rear_left", top: 80, left: 16 },
  { key: "rear_right", top: 80, left: 84 },
];

class RvLevelVehicleCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._built = false;
  }

  setConfig(config) {
    for (const corner of RVL_CORNERS) {
      const key = `${corner.key}_entity`;
      if (!config[key]) {
        throw new Error(`rv-level-vehicle-card: '${key}' is required`);
      }
    }
    if (!config.level_entity) {
      throw new Error("rv-level-vehicle-card: 'level_entity' is required");
    }
    this._config = { title: "Vehicle", ...config };
    this._built = false;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 6;
  }

  static getStubConfig() {
    return {
      title: "Vehicle",
      front_left_entity: "sensor.rv_level_front_left_chock",
      front_right_entity: "sensor.rv_level_front_right_chock",
      rear_left_entity: "sensor.rv_level_rear_left_chock",
      rear_right_entity: "sensor.rv_level_rear_right_chock",
      level_entity: "binary_sensor.rv_level_level",
      levelable_entity: "binary_sensor.rv_level_levelable",
    };
  }

  _build() {
    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .rvv-title {
          font-size: 1rem;
          font-weight: 500;
          color: var(--primary-text-color);
          margin-bottom: 8px;
        }
        .rvv-stage {
          position: relative;
          width: 100%;
          max-width: 260px;
          aspect-ratio: 200 / 320;
          margin: 0 auto;
          color: var(--secondary-text-color);
        }
        .rvv-stage img, .rvv-stage svg {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          object-fit: contain;
        }
        .rvv-badge {
          position: absolute;
          transform: translate(-50%, -50%);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
          background: var(--card-background-color, #fff);
          border: 1px solid var(--divider-color);
          border-radius: 10px;
          padding: 4px 8px;
          font-size: 0.75rem;
          color: var(--primary-text-color);
          min-width: 44px;
          text-align: center;
        }
        .rvv-badge ha-icon {
          --mdc-icon-size: 20px;
          color: var(--disabled-text-color, #888);
        }
        .rvv-badge.rvv-active ha-icon {
          color: var(--info-color, var(--primary-color));
        }
        .rvv-status {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          font-weight: 500;
          font-size: 0.8rem;
        }
        .rvv-status ha-icon {
          --mdc-icon-size: 32px;
        }
        .rvv-missing {
          color: var(--error-color, #e74c3c);
          padding: 8px 0;
        }
      </style>
      <ha-card>
        <div class="rvv-title"></div>
        <div class="rvv-stage">
          <div class="rvv-image"></div>
          <div class="rvv-badge" data-corner="front_left"><ha-icon></ha-icon><span></span></div>
          <div class="rvv-badge" data-corner="front_right"><ha-icon></ha-icon><span></span></div>
          <div class="rvv-badge" data-corner="rear_left"><ha-icon></ha-icon><span></span></div>
          <div class="rvv-badge" data-corner="rear_right"><ha-icon></ha-icon><span></span></div>
          <div class="rvv-status"><ha-icon></ha-icon><span></span></div>
        </div>
        <div class="rvv-missing" hidden></div>
      </ha-card>
    `;
    this._titleEl = this.shadowRoot.querySelector(".rvv-title");
    this._imageEl = this.shadowRoot.querySelector(".rvv-image");
    this._stageEl = this.shadowRoot.querySelector(".rvv-stage");
    this._missingEl = this.shadowRoot.querySelector(".rvv-missing");
    this._statusEl = this.shadowRoot.querySelector(".rvv-status");
    this._statusIcon = this._statusEl.querySelector("ha-icon");
    this._statusLabel = this._statusEl.querySelector("span");
    this._badges = {};
    for (const corner of RVL_CORNERS) {
      const el = this.shadowRoot.querySelector(`.rvv-badge[data-corner="${corner.key}"]`);
      el.style.top = `${corner.top}%`;
      el.style.left = `${corner.left}%`;
      this._badges[corner.key] = {
        el,
        icon: el.querySelector("ha-icon"),
        label: el.querySelector("span"),
      };
    }

    if (this._config.image) {
      this._imageEl.innerHTML = `<img src="${this._config.image}" alt="Vehicle top view">`;
    } else {
      this._imageEl.innerHTML = RVL_GENERIC_VAN_SVG;
    }

    this._built = true;
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._built) this._build();

    this._titleEl.textContent = this._config.title || "";

    const missing = [];
    for (const corner of RVL_CORNERS) {
      const entityId = this._config[`${corner.key}_entity`];
      if (!this._hass.states[entityId]) missing.push(entityId);
    }
    if (!this._hass.states[this._config.level_entity]) {
      missing.push(this._config.level_entity);
    }
    if (missing.length) {
      this._stageEl.hidden = true;
      this._missingEl.hidden = false;
      this._missingEl.textContent = `Entity not found: ${missing.join(", ")}`;
      return;
    }
    this._stageEl.hidden = false;
    this._missingEl.hidden = true;

    for (const corner of RVL_CORNERS) {
      const state = this._hass.states[this._config[`${corner.key}_entity`]];
      const index = Number(state.attributes.chock_index ?? (Number(state.state) > 0 ? 1 : 0));
      const badge = this._badges[corner.key];
      badge.icon.setAttribute("icon", rvlIconForChockIndex(index));
      badge.label.textContent = rvlFormatCm(state.state);
      badge.el.classList.toggle("rvv-active", index > 0);
    }

    const isLevel = this._hass.states[this._config.level_entity].state === "on";
    const levelableState = this._config.levelable_entity
      ? this._hass.states[this._config.levelable_entity]
      : undefined;
    const isLevelable = levelableState ? levelableState.state === "on" : true;

    let icon;
    let label;
    let color;
    if (isLevel) {
      icon = "mdi:thumb-up";
      label = "Level";
      color = "var(--success-color, #2ecc71)";
    } else if (!isLevelable) {
      icon = "mdi:close-octagon";
      label = "Not levelable";
      color = "var(--error-color, #e74c3c)";
    } else {
      icon = "mdi:thumb-down";
      label = "Not level";
      color = "var(--warning-color, #f39c12)";
    }
    this._statusIcon.setAttribute("icon", icon);
    this._statusIcon.style.color = color;
    this._statusLabel.textContent = label;
    this._statusLabel.style.color = color;
  }
}

customElements.define("rv-level-vehicle-card", RvLevelVehicleCard);

// ---------------------------------------------------------------------
// Card picker registration
// ---------------------------------------------------------------------

window.customCards = window.customCards || [];
window.customCards.push(
  {
    type: "rv-level-bubble-card",
    name: "RV Level: Bubble",
    description: "Circular bubble-level indicator for the RV Level integration.",
    preview: false,
  },
  {
    type: "rv-level-vehicle-card",
    name: "RV Level: Vehicle overview",
    description: "Top-down per-wheel chock/lift overview for the RV Level integration.",
    preview: false,
  }
);
