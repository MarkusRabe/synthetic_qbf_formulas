
import normalize

# print(normalize._qdimacs_to_clauselist('test_sat.qdimacs'))

# print(normalize._clauses_to_occs([[1,2,3],[1],[1,2]]))

print(normalize.read_and_normalize('test_sat.qdimacs'))

