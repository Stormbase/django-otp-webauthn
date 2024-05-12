// Functions provided by Django's JavaScript translation catalog
declare function gettext(msgid: string): string;
declare function ngettext(
  msgid: string,
  msgid_plural: string,
  count: number,
): string;
declare function interpolate(
  formats: string,
  values: any[],
  named: boolean,
): string;
declare function get_format(format_type: string): string;
declare function gettext_noop(msgid: string): string;
declare function pgettext(context: string, msgid: string): string;
declare function npgettext(
  context: string,
  msgid: string,
  msgid_plural: string,
  count: number,
): string;
declare function pluralidx(count: number): boolean;
