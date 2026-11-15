import { mockCases } from '../data/mockCases'
import { API_BASE_URL, USE_MOCK_DATA } from './config'

export type Case = (typeof mockCases)[number]
export type SearchResult = Case & {
  score: number
}

export async function searchCases(query: string): Promise<SearchResult[]> {
    //Use backend when mock data is disabled
    if (!USE_MOCK_DATA){
      //Backend request code
      const response = await fetch(`${API_BASE_URL}/cases/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    })

    if (!response.ok) {
      throw new Error('Failed to retrieve cases')
    }

    const data: SearchResult[] = await response.json()
    return data
  }
  
  // Temporary mock search until the backend is connected
  const normalizedQuery = query.toLowerCase().trim()

  const results = mockCases
    .map((caseItem) => {
      let score = 0

      if (normalizedQuery !== '') {
        if (caseItem.title.toLowerCase().includes(normalizedQuery)) {
          score += 3
        }

        if (
          caseItem.symptoms.some((symptom) =>
            symptom.toLowerCase().includes(normalizedQuery)
          )
        ) {
          score += 2
        }

        if (caseItem.summary.toLowerCase().includes(normalizedQuery)) {
          score += 1
        }
      }

      return { ...caseItem, score }
    })
    .filter((caseItem) => normalizedQuery === '' || caseItem.score > 0)
    .sort((a, b) => b.score - a.score)

  return results
}
