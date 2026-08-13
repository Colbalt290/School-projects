def filterbadbad():
    print("Type to chat in chat!: ")
    lewords = input("")
    lebadwords = ["stupidest", "stupider", "stupid"]

    for word in lebadwords:
      if word in lewords.lower():
        lewords = lewords.replace(word,"*" * len(word))
        #^ This replaces the words with asterisks.
    print(lewords)

filterbadbad()