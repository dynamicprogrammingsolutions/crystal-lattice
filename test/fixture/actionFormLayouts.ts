import type { ActionDisplayPayload, ActionDialog } from '@crystal-lattice/frontend-sdk';

export const THREE_FIELD_DIALOG = {
  kind: 'form',
  title: 'Edit fixture values',
  inputs: [
    {
      name: 'first',
      label: 'First value',
      type: 'string',
      default: 'first value',
      required: true,
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'multiline',
      default: 'fixture notes',
    },
    {
      name: 'last',
      label: 'Last value',
      type: 'string',
      default: 'last value',
    },
  ],
} satisfies ActionDialog;

export const MANY_FIELD_DIALOG = {
  kind: 'form',
  title: 'Edit many fixture values',
  inputs: [
    ...Array.from({ length: 18 }, (_, index) => ({
      name: `value_${index}`,
      label: `Value ${index}`,
      description: 'A fixture field with supporting text that wraps on a narrow screen.',
      type: index % 5 === 0 ? 'multiline' : 'string',
      default: `initial ${index}`,
      required: true,
    })),
    { name: 'count', label: 'Count', type: 'integer', default: 7 },
    {
      name: 'last',
      label: 'Last value',
      type: 'string',
      default: 'last value',
      required: true,
    },
  ],
} satisfies ActionDialog;

export const LONG_LAYOUT_MARKDOWN = [
  '# Fixture report',
  ...Array.from(
    { length: 80 },
    (_, index) =>
      `Paragraph ${index}: A neutral report with **important values** and enough content to require scrolling.`,
  ),
  'REPORT END',
].join('\n\n');

export function buildLayoutDisplay(fieldCount = 0): ActionDisplayPayload {
  return {
    title: 'Fixture report',
    format: 'markdown',
    body: LONG_LAYOUT_MARKDOWN,
    presentation: 'modal',
    form: fieldCount
      ? {
          kind: 'form',
          inputs:
            fieldCount === 2
              ? [
                  {
                    name: 'from',
                    label: 'From',
                    type: 'string',
                    default: 'first bound',
                    submit_empty: true,
                  },
                  {
                    name: 'to',
                    label: 'To',
                    type: 'string',
                    default: 'last bound',
                    submit_empty: true,
                  },
                ]
              : MANY_FIELD_DIALOG.inputs,
        }
      : undefined,
    actions: [
      {
        kind: 'run_action',
        id: 'apply',
        label: 'Apply values',
        plugin: 'layout_fixture',
        action_id: 'apply',
        preserve_display: true,
      },
      {
        kind: 'run_action',
        id: 'edit',
        label: 'Open form',
        plugin: 'layout_fixture',
        action_id: 'edit',
        preserve_display: true,
        dialog: MANY_FIELD_DIALOG,
      },
      { kind: 'dismiss', id: 'close', label: 'Close report' },
    ],
  };
}
