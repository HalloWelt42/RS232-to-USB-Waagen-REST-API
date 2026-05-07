/** Schnell-Vorlagen für den Zähl-Modus. */

export interface CountTemplate {
  id: string;
  label: string;
  iconClass: string;        // FA-Klasse, ohne 'fa-' Präfix
  pieceWeightG: number;     // typisches Stückgewicht
  description: string;
}

export const COUNT_TEMPLATES: readonly CountTemplate[] = [
  {
    id: 'screws',
    label: 'Schrauben',
    iconClass: 'fa-solid fa-screwdriver-wrench',
    pieceWeightG: 2.8,
    description: 'M5×20-Standardgewinde, ca. 2,8 g/Stück.',
  },
  {
    id: 'tablets',
    label: 'Tabletten',
    iconClass: 'fa-solid fa-pills',
    pieceWeightG: 0.5,
    description: 'Standardtablette ca. 0,5 g/Stück (bitte selbst kalibrieren).',
  },
  {
    id: 'coins',
    label: 'Münzen',
    iconClass: 'fa-solid fa-coins',
    pieceWeightG: 8.5,
    description: '2-Euro-Münze 8,5 g/Stück. Andere Münzen abweichend.',
  },
  {
    id: 'envelopes',
    label: 'Briefe',
    iconClass: 'fa-solid fa-envelope',
    pieceWeightG: 12.0,
    description: 'Standardbrief ca. 12 g/Stück mit Inhalt.',
  },
] as const;
