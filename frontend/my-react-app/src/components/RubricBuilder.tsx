import { useState } from 'react'

import type { RubricCriterion } from '../types/feedback'

type Props = {
  rubric: RubricCriterion[]
  onChange: (criteria: RubricCriterion[]) => void
}

const emptyCriterion: RubricCriterion = { name: '', max_points: 20, description: '' }

export default function RubricBuilder({ rubric, onChange }: Props) {
  const [draft, setDraft] = useState<RubricCriterion>(emptyCriterion)

  const addCriterion = () => {
    if (!draft.name.trim() || !draft.description.trim()) return
    onChange([...rubric, draft])
    setDraft(emptyCriterion)
  }

  return (
    <section className="panel">
      <h2>Rubric Criteria</h2>
      <div className="field">
        <input
          placeholder="Criterion name"
          value={draft.name}
          onChange={(e) => setDraft({ ...draft, name: e.target.value })}
        />
      </div>
      <div className="field">
        <input
          type="number"
          min={1}
          placeholder="Max points"
          value={draft.max_points}
          onChange={(e) => setDraft({ ...draft, max_points: Number(e.target.value) })}
        />
      </div>
      <div className="field">
        <textarea
          placeholder="Criterion description"
          value={draft.description}
          onChange={(e) => setDraft({ ...draft, description: e.target.value })}
        />
      </div>
      <button className="primary-btn" type="button" onClick={addCriterion}>
        Add Criterion
      </button>
      <ul className="rubric-list">
        {rubric.map((item) => (
          <li key={`${item.name}-${item.max_points}`}>
            {item.name} ({item.max_points}): {item.description}
          </li>
        ))}
      </ul>
    </section>
  )
}
