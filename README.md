You need to install LM Studio for this to work, then open it to network. You will also need
to provide your own text corpus. After that, it works more or less like a full-text search
engine & summarizer. The summarizer is very flaky, and prone to hallucinations. If that's
your thing, then have fun. It will be a wild time.

See my article where I reverse engineer a hallucination here: [TODO]

This uses pretty much only standard library stuff, with the only
package being Weaviate, which is the vector database. I am using
the vector database only to store embeddings I calculate from
LM Studio's models. There is a pre-cooked way to do this in
Weaviate. I prefer home cooking, personally, so this system
controls the vectorization process itself.
