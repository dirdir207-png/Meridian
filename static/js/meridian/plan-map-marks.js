/* Which concept mark and which kit glyph a Plan allocation station gets.
 *
 * DOM-free on purpose, so a Node round-trip can exercise every label case (see
 * tests/meridian/test_plan_map_marks.py). The mapping used to live inside plan.js, where the
 * only possible guard was a text match on the source -- and a text match cannot see that two
 * different labels resolve to the same mark, which is exactly the regression the owner
 * caught on 2026-09-24: "the right still says unfounded commitments and has the same icon as
 * committed to commitments".
 *
 * WHY THE ORDER OF THESE TESTS MATTERS. "Unfunded commitments" contains the word
 * "commitments", so a broad `/commit/` test placed BEFORE the shortfall case hands the Bills
 * station's rotunda and bank glyph to a SHORTFALL. The service's labels and this module ship
 * at different moments -- the running app kept serving the old segment labels while a new
 * mapping was already live in the browser -- so the interim state is a real state that must
 * be correct on its own, not just after a deploy.
 *
 * `null` means "keep the kit fallback", which is what a shortfall or an unrecognised label
 * must do rather than borrowing a station's meaning.
 */

/* `unfunded` must be checked before `bills`, for the reason above. */
export function allocationIcon(label) {
  if (/available/i.test(label)) return "compass";
  if (/goal/i.test(label)) return "flag";
  if (/unfund/i.test(label)) return "bell";
  if (/bill/i.test(label) || /commit/i.test(label)) return "bank";
  return "bell";
}

/* The three marks the governing concept actually draws (02-plan.png), generated as RAISED
   brass rasters on 2026-09-23 under D-021 and delivered in
   design/plan-map-marks-2026-09-23/: a domed rotunda for money already committed, a flagged
   mountain summit for a goal, and ONE eight-point star rose that the concept uses at two
   sizes -- large for the map's hub and small for Available. Nothing else has a concept
   original, so nothing else gets one. */
export function allocationMark(label) {
  if (/available/i.test(label)) return "star-rose";
  if (/goal/i.test(label)) return "mountain-flag";
  if (/unfund/i.test(label)) return null;
  if (/bill/i.test(label) || /commit/i.test(label)) return "rotunda";
  return null;
}
