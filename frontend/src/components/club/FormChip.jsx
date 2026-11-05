import { RESULT_LABELS } from '../../utils/matches'

// A W / D / L square. The letter is always shown, so the colour is never the only clue.
function FormChip({ result }) {
  return (
    <span className={`club-form club-form--${result}`} role="img" aria-label={RESULT_LABELS[result]}>
      {result}
    </span>
  )
}

export default FormChip
