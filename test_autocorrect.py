import unittest
from autocorrect import spell

def correct_sentence(sentence):
	words = sentence.split()
	for word in words:
		word = spell(word)
	return " ".join(words)

class TestAutoCorrect(unittest.TestCase):
	def test_autocorrect(self):
		self.assertEqual(correct_sentence("How ar you ?"),"How are you ?")
		self.assertEqual(correct_sentence("I lost my crd ."),"I lost my card .")
		self.assertEqual(correct_sentence("Wen is te dedline for documnts?"),"When is the deadline for documents?")
		self.assertEqual(correct_sentence("Can yu hep me wit isue?"),"Can you help me with issue?")

if __name__ == '__main__':
	unittest.main()