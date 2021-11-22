from app import db

def ratings(room):
    cursor = db.connection.cursor()
    cursor.execute("""SELECT reviewsRating FROM reviews WHERE reviewsEssayId = %s""", (room,))
    ratings = cursor.fetchall()
    if ratings == None:
        return 0
    else:
        total = 0
        rate = []
        for value in ratings:
            for x in value:
                rate.append(x)
                print(rate)
            for num in rate:
                total += num
        return total/len(ratings)

ratings(1)