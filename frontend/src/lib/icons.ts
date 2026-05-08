/**
 * Kuratierte FontAwesome-Icons für den IconPicker.
 *
 * Nicht alle ~2000 FA-Free-Icons sind sinnvoll für eine Wäge-App —
 * die hier aufgeführten passen zu typischen Stückzähl-Anwendungen
 * (Werkstatt, Apotheke, Bäckerei, Versand, Münzen, Schmuck) und
 * sind alle in `@fortawesome/fontawesome-free` enthalten (Solid +
 * Regular).
 *
 * `keywords` enthält deutsche und englische Suchbegriffe — die
 * Suche im Picker matcht case-insensitive auf das Tupel
 * `[icon-class, label, keywords]`.
 */

export interface IconEntry {
  /** FontAwesome-Klasse, wie sie als `<i class="...">` verwendet wird. */
  cls: string;
  /** Kurzer Anzeige-Name beim Hover. */
  label: string;
  /** Suchbegriffe — DE und EN gemischt, der Picker matcht substring. */
  keywords: string;
}

export const ICONS: readonly IconEntry[] = [
  // -------- Standard / Universal --------
  { cls: 'fa-solid fa-cube',                 label: 'Würfel',          keywords: 'cube würfel box element default standard' },
  { cls: 'fa-solid fa-cubes',                label: 'Würfel-Stapel',   keywords: 'cubes würfel stapel pile blöcke' },
  { cls: 'fa-solid fa-shapes',               label: 'Formen',          keywords: 'shapes formen geometrie objekte teile' },
  { cls: 'fa-solid fa-circle',               label: 'Kreis',           keywords: 'circle kreis dot punkt' },
  { cls: 'fa-solid fa-square',               label: 'Quadrat',         keywords: 'square quadrat' },

  // -------- Werkstatt / Werkzeuge --------
  { cls: 'fa-solid fa-screwdriver-wrench',   label: 'Schraubenzieher', keywords: 'schraube screw nail werkzeug tool werkstatt' },
  { cls: 'fa-solid fa-wrench',               label: 'Schraubenschlüssel', keywords: 'wrench schlüssel werkzeug' },
  { cls: 'fa-solid fa-hammer',               label: 'Hammer',          keywords: 'hammer werkzeug' },
  { cls: 'fa-solid fa-screwdriver',          label: 'Schraubenzieher (klein)', keywords: 'schraubenzieher schraube' },
  { cls: 'fa-solid fa-toolbox',              label: 'Werkzeugkasten',  keywords: 'werkzeugkasten toolbox' },
  { cls: 'fa-solid fa-gears',                label: 'Zahnräder',       keywords: 'gears zahnräder mechanik teile' },
  { cls: 'fa-solid fa-bolt',                 label: 'Blitz/Bolzen',    keywords: 'bolt blitz bolzen' },
  { cls: 'fa-solid fa-link',                 label: 'Glied',           keywords: 'link glied kette chain' },

  // -------- Apotheke / Tabletten --------
  { cls: 'fa-solid fa-pills',                label: 'Tabletten',       keywords: 'pills tabletten medizin pharma kapsel' },
  { cls: 'fa-solid fa-capsules',             label: 'Kapseln',         keywords: 'capsules kapseln tabletten' },
  { cls: 'fa-solid fa-prescription-bottle',  label: 'Tabletten-Glas',  keywords: 'prescription bottle tablettenglas' },
  { cls: 'fa-solid fa-prescription-bottle-medical', label: 'Tabletten-Dose', keywords: 'medical bottle' },
  { cls: 'fa-solid fa-syringe',              label: 'Spritze',         keywords: 'syringe spritze injektion' },
  { cls: 'fa-solid fa-mortar-pestle',        label: 'Mörser',          keywords: 'mortar pestle mörser apotheke' },
  { cls: 'fa-solid fa-flask',                label: 'Flasche',         keywords: 'flask flasche labor chemie' },
  { cls: 'fa-solid fa-vial',                 label: 'Reagenzglas',     keywords: 'vial reagenzglas labor' },
  { cls: 'fa-solid fa-vials',                label: 'Reagenzgläser',   keywords: 'vials reagenzgläser labor' },

  // -------- Münzen / Geld --------
  { cls: 'fa-solid fa-coins',                label: 'Münzen',          keywords: 'coins münzen geld geldstück' },
  { cls: 'fa-solid fa-money-bill',           label: 'Geldschein',      keywords: 'money bill geldschein note' },
  { cls: 'fa-solid fa-money-bill-1',         label: 'Schein (1)',      keywords: 'money bill schein' },
  { cls: 'fa-solid fa-piggy-bank',           label: 'Sparschwein',     keywords: 'piggy bank sparschwein sparen' },
  { cls: 'fa-solid fa-vault',                label: 'Tresor',          keywords: 'vault tresor safe' },
  { cls: 'fa-solid fa-sack-dollar',          label: 'Geldsack',        keywords: 'sack dollar geldsack' },

  // -------- Versand / Briefe --------
  { cls: 'fa-solid fa-envelope',             label: 'Brief',           keywords: 'envelope brief mail post' },
  { cls: 'fa-solid fa-envelopes-bulk',       label: 'Briefe (Stapel)', keywords: 'envelopes bulk briefe stapel post' },
  { cls: 'fa-solid fa-stamp',                label: 'Briefmarke',      keywords: 'stamp briefmarke marke' },
  { cls: 'fa-solid fa-box',                  label: 'Paket',           keywords: 'box paket karton package' },
  { cls: 'fa-solid fa-boxes-stacked',        label: 'Pakete (Stapel)', keywords: 'boxes stacked pakete stapel lager' },
  { cls: 'fa-solid fa-box-open',             label: 'Paket offen',     keywords: 'box open paket offen' },
  { cls: 'fa-solid fa-truck',                label: 'LKW',             keywords: 'truck lkw versand transport' },

  // -------- Lebensmittel / Bäckerei / Küche --------
  { cls: 'fa-solid fa-bread-slice',          label: 'Brot-Scheibe',    keywords: 'bread slice brot scheibe bäckerei' },
  { cls: 'fa-solid fa-cookie',               label: 'Keks',            keywords: 'cookie keks gebäck bäckerei' },
  { cls: 'fa-solid fa-cookie-bite',          label: 'Keks (gebissen)', keywords: 'cookie bite keks' },
  { cls: 'fa-solid fa-egg',                  label: 'Ei',              keywords: 'egg ei' },
  { cls: 'fa-solid fa-apple-whole',          label: 'Apfel',           keywords: 'apple apfel obst' },
  { cls: 'fa-solid fa-lemon',                label: 'Zitrone',         keywords: 'lemon zitrone obst' },
  { cls: 'fa-solid fa-pepper-hot',           label: 'Chili',           keywords: 'pepper chili gewürz' },
  { cls: 'fa-solid fa-carrot',               label: 'Karotte',         keywords: 'carrot karotte gemüse' },
  { cls: 'fa-solid fa-fish',                 label: 'Fisch',           keywords: 'fish fisch' },
  { cls: 'fa-solid fa-drumstick-bite',       label: 'Hähnchenbein',    keywords: 'drumstick hähnchen fleisch' },
  { cls: 'fa-solid fa-bacon',                label: 'Speck',           keywords: 'bacon speck fleisch' },
  { cls: 'fa-solid fa-cheese',               label: 'Käse',            keywords: 'cheese käse' },
  { cls: 'fa-solid fa-cake-candles',         label: 'Kuchen',          keywords: 'cake candles kuchen torte' },
  { cls: 'fa-solid fa-ice-cream',            label: 'Eis',             keywords: 'ice cream eis' },
  { cls: 'fa-solid fa-mug-hot',              label: 'Kaffee',          keywords: 'mug hot kaffee tasse tee' },
  { cls: 'fa-solid fa-wine-bottle',          label: 'Weinflasche',     keywords: 'wine bottle wein flasche' },
  { cls: 'fa-solid fa-bottle-water',         label: 'Wasserflasche',   keywords: 'bottle water wasser flasche' },

  // -------- Schmuck --------
  { cls: 'fa-solid fa-gem',                  label: 'Edelstein',       keywords: 'gem edelstein juwel diamant schmuck' },
  { cls: 'fa-solid fa-ring',                 label: 'Ring',            keywords: 'ring schmuck' },
  { cls: 'fa-solid fa-crown',                label: 'Krone',           keywords: 'crown krone' },

  // -------- Garten / Pflanzen / Saatgut --------
  { cls: 'fa-solid fa-seedling',             label: 'Setzling',        keywords: 'seedling setzling pflanze samen saat' },
  { cls: 'fa-solid fa-leaf',                 label: 'Blatt',           keywords: 'leaf blatt pflanze' },
  { cls: 'fa-solid fa-tree',                 label: 'Baum',            keywords: 'tree baum pflanze' },
  { cls: 'fa-solid fa-wheat-awn',            label: 'Weizen',          keywords: 'wheat weizen getreide' },

  // -------- Tiere / Bienen --------
  { cls: 'fa-solid fa-paw',                  label: 'Pfote',           keywords: 'paw pfote tier' },
  { cls: 'fa-solid fa-bug',                  label: 'Käfer',           keywords: 'bug käfer insekt' },

  // -------- Industrie / Material --------
  { cls: 'fa-solid fa-industry',              label: 'Industrie',       keywords: 'industry industrie fabrik' },
  { cls: 'fa-solid fa-warehouse',             label: 'Lager',           keywords: 'warehouse lager halle' },
  { cls: 'fa-solid fa-pallet',                label: 'Palette',         keywords: 'pallet palette logistik' },
  { cls: 'fa-solid fa-dolly',                 label: 'Sackkarre',       keywords: 'dolly sackkarre handkarren' },
  { cls: 'fa-solid fa-helmet-safety',         label: 'Helm',            keywords: 'helmet safety helm bauhelm' },

  // -------- Office / Büro --------
  { cls: 'fa-solid fa-paperclip',             label: 'Büroklammer',     keywords: 'paperclip büroklammer klammer' },
  { cls: 'fa-solid fa-thumbtack',             label: 'Reißzwecke',      keywords: 'thumbtack reißzwecke nadel' },
  { cls: 'fa-solid fa-sticky-note',           label: 'Notiz',           keywords: 'sticky note notiz zettel' },
  { cls: 'fa-solid fa-pen',                   label: 'Stift',           keywords: 'pen stift kugelschreiber' },
  { cls: 'fa-solid fa-clipboard-list',        label: 'Klemmbrett',      keywords: 'clipboard klemmbrett liste' },

  // -------- Sonstige Objekte --------
  { cls: 'fa-solid fa-key',                   label: 'Schlüssel',       keywords: 'key schlüssel' },
  { cls: 'fa-solid fa-puzzle-piece',          label: 'Puzzle',          keywords: 'puzzle teil stück' },
  { cls: 'fa-solid fa-cake',                  label: 'Geschenk',        keywords: 'gift geschenk' },
  { cls: 'fa-solid fa-gift',                  label: 'Geschenk',        keywords: 'gift geschenk päckchen' },
  { cls: 'fa-solid fa-tag',                   label: 'Etikett',         keywords: 'tag etikett label' },
  { cls: 'fa-solid fa-tags',                  label: 'Etiketten',       keywords: 'tags etiketten labels' },
  { cls: 'fa-solid fa-barcode',               label: 'Barcode',         keywords: 'barcode strichcode' },
  { cls: 'fa-solid fa-qrcode',                label: 'QR-Code',         keywords: 'qrcode qr code' },
  { cls: 'fa-solid fa-battery-full',          label: 'Batterie',        keywords: 'battery batterie akku' },
  { cls: 'fa-solid fa-microchip',             label: 'Mikrochip',       keywords: 'microchip chip ic elektronik' },
  { cls: 'fa-solid fa-plug',                  label: 'Stecker',         keywords: 'plug stecker' },

  // -------- Sport / Spiel --------
  { cls: 'fa-solid fa-baseball',              label: 'Baseball',        keywords: 'baseball ball' },
  { cls: 'fa-solid fa-football',              label: 'Football',        keywords: 'football ball' },
  { cls: 'fa-solid fa-dice',                  label: 'Würfel',          keywords: 'dice würfel spiel' },
  { cls: 'fa-solid fa-chess-knight',          label: 'Springer',        keywords: 'chess knight springer schach' },

  // -------- Sonstiges Praktisches --------
  { cls: 'fa-solid fa-droplet',               label: 'Tropfen',         keywords: 'droplet tropfen flüssigkeit' },
  { cls: 'fa-solid fa-fire',                  label: 'Feuer',           keywords: 'fire feuer' },
  { cls: 'fa-solid fa-snowflake',             label: 'Schneeflocke',    keywords: 'snowflake schnee kalt frost' },
  { cls: 'fa-solid fa-magnet',                label: 'Magnet',          keywords: 'magnet' },
  { cls: 'fa-solid fa-anchor',                label: 'Anker',           keywords: 'anchor anker' },
  { cls: 'fa-solid fa-feather',               label: 'Feder',           keywords: 'feather feder' },
  { cls: 'fa-solid fa-shoe-prints',           label: 'Fußabdruck',      keywords: 'shoe prints fußabdruck' },
];

/** Filtert die Icon-Liste anhand eines Suchstrings (substring, case-insensitive). */
export function filterIcons(query: string): readonly IconEntry[] {
  const q = query.trim().toLowerCase();
  if (!q) return ICONS;
  return ICONS.filter(
    (i) =>
      i.cls.toLowerCase().includes(q) ||
      i.label.toLowerCase().includes(q) ||
      i.keywords.toLowerCase().includes(q),
  );
}
