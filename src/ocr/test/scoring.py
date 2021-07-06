import editdistance

# class that helps to determine accuracy of a single block or test set in general
class Scoring:

    def __init__(self):
        self.block_results = list()

    # returns the ocr score for the new (or original) ocr 
    def get_score(self, block, new_ocr=True, average=False):

        string1 = block.ocr_gt
        string2 = block.ocr

        if not new_ocr:
            string2 = block.ocr_ori

        nchars = max(1, len(string1))
        if average:
            nchars = max(1, (len(string1)+len(string2))/2.0)
        total_edit = editdistance.eval(string1, string2)
        final_score = total_edit/nchars
        self.block_results.append((total_edit, nchars))

        return max(0, (1.0-final_score))

    # returns the score for a set of blocks, computed through weighting the individual blocks using their char length
    def get_set_score(self):
        if len(self.block_results) == 0:
            return None
        total_edit = 0
        total_chars = 0
        for result in self.block_results:
            total_edit += result[0]
            total_chars += result[1]
        final_score = total_edit/total_chars
        return max(0, (1.0-final_score))