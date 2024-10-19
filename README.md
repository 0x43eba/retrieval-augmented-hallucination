You need to install LM Studio for this to work, then open it to network.

I'm using this for a personal project. My objective is to create a system where 
I talk to the sum total of the world's:

- Constitutions
- Legal/penal codes
- Civil Codes
- Popular political discourse
- Ideological perspectives

I opted for the LM Studio models, since OpenAI's safety protocols
were causing problems when being asked to embed or analyze,
policies, and political ideologies which are contrary to
western values. It is impossible to study the world's political
systems, when the only things we are allowed to ask LLMs about,
are the things that align with our values. It shelters us,
and (in the worst case) normalizees our abnormal level of
personal freedom and safety.

Most of the world does not live like we do in the west. Most of 
the world isn't free. We need a way to leverage the incredible
computing power that is available now, to understand this.

Laws and ideologies range from sunshine and rainbows, to horrific violations
of basic decency. This system is designed to, without training-wheels, 
simply tell me what the ideas and laws are. There is no centralized way to 
do this now. This is going to do that.

This uses pretty much only standard library stuff, with the only
package being Weaviate, which is the vector database. I am using
the vector database only to store embeddings I calculate from
LM Studio's models. There is a pre-cooked way to do this in
Weaviate. I prefer home cooking, personally, so this system
controls the vectorization process itself.