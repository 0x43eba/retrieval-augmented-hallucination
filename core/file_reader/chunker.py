def sliding_window_split(text, window_size, overlap):
    words = text.split()
    chunks = []
    for i in range(0, len(words), window_size - overlap):
        chunk = words[i:i + window_size]
        chunks.append(" ".join(chunk))
    return chunks
