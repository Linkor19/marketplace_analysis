import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from data_gen import (users, user_profiles, listings, listing_promotions,
                      view_bookings, deals, partner_discounts, clickstream_events,
                      cities_df, categories_df)

pd.options.display.max_columns = None
pd.set_option('display.width', 9999)

# end-to-end table listing -> booking -> deal; relations are 1:1, so the join does not duplicate rows
listing_deal = (listings
                .merge(view_bookings[['booking_id', 'listing_id', 'buyer_id', 'status']]
                       .rename(columns={'status': 'статус_броні'}), on='listing_id', how='left')
                .merge(deals[['deal_id', 'booking_id', 'deal_amount', 'closed_at']], on='booking_id', how='left')
                .merge(users[['user_id', 'country']].rename(columns={'user_id': 'seller_id', 'country': 'країна'}),
                       on='seller_id', how='left')
                .merge(cities_df[['city_id', 'city_name']], on='city_id', how='left')
                .merge(listing_promotions[['listing_id', 'amount_paid']], on='listing_id', how='left'))

# join integrity control: the number of rows must equal the number of listings
print(f'оголошень: {len(listings)}, рядків після join: {len(listing_deal)}')

######################################################################################################################## Task 2 - funnel Registration -> Profile -> Discount

# unfold the clickstream into a wide table: row - user, column - funnel step
events_wide = clickstream_events.pivot_table(index='user_id', columns='event_type', values='event_id', aggfunc='count')
user_journey = users[['user_id', 'country']].merge(events_wide, on='user_id', how='left').fillna(0)

steps = ['user_registered', 'pet_profile_created', 'partner_discount_used']
for step in steps:
    user_journey[step] = (user_journey[step] > 0).astype(int)  # flag of the fact of the event, not its count

# tracking audit: the registration event must be present for 100% of users, otherwise the clickstream is incomplete
print(f"користувачів у БД: {len(users)}, з подією user_registered: {user_journey['user_registered'].sum()}")

funnel_country = user_journey.groupby('country')[steps].sum().reset_index()
funnel_country.columns = ['країна', 'реєстрація', 'профіль_улюбленця', 'знижка_партнера']
funnel_country['cr_реєстрація_профіль_%'] = (funnel_country['профіль_улюбленця'] / funnel_country['реєстрація'] * 100).round(2)
funnel_country['cr_профіль_знижка_%'] = (funnel_country['знижка_партнера'] / funnel_country['профіль_улюбленця'] * 100).round(2)
funnel_country['cr_наскрізна_%'] = (funnel_country['знижка_партнера'] / funnel_country['реєстрація'] * 100).round(2)
print('--- Task 2: воронка Реєстрація -> Профіль -> Знижка ---')
print(funnel_country)

# z-test on the difference of registration -> profile conversions between the UA and PL markets
ua = user_journey[user_journey['country'] == 'UA']
pl = user_journey[user_journey['country'] == 'PL']
cr_ua = ua['pet_profile_created'].mean()
cr_pl = pl['pet_profile_created'].mean()
ppool = (ua['pet_profile_created'].sum() + pl['pet_profile_created'].sum()) / (len(ua) + len(pl))
SEppool = np.sqrt(ppool * (1 - ppool) * (1 / len(ua) + 1 / len(pl)))
z = (cr_ua - cr_pl) / SEppool
print(f'cr UA = {cr_ua:.4f}, cr PL = {cr_pl:.4f}, z-score = {z:.3f}')
if abs(z) > 1.96:
    print('різниця конверсій між ринками статистично значуща')
else:
    print('різниця конверсій між ринками статистично не значуща - ринки поводяться однаково')
# segment: does the use of the partner discount depend on the pet type
pet_profiles = user_profiles[user_profiles['has_pet_profile']].merge(
    partner_discounts[['user_id', 'discount_id']], on='user_id', how='left')
pet_segment = pet_profiles.groupby('pet_type').agg(
    профілі=('user_id', 'count'), знижки=('discount_id', 'count')).reset_index()
pet_segment['cr_знижка_%'] = (pet_segment['знижки'] / pet_segment['профілі'] * 100).round(2)
pet_segment = pet_segment.rename(columns={'pet_type': 'тип_улюбленця'})
print(pet_segment)

# segment: does the pet profile convert into real activity on the platform
activity = user_profiles[['user_id', 'has_pet_profile']].copy()
activity['покупець'] = activity['user_id'].isin(view_bookings['buyer_id'])
activity['продавець'] = activity['user_id'].isin(listings['seller_id'])
activity_segment = activity.groupby('has_pet_profile')[['покупець', 'продавець']].mean().round(4).reset_index()
print(activity_segment.rename(columns={'has_pet_profile': 'є_профіль_улюбленця'}))

sns.barplot(x='країна', y='value', hue='variable',
            data=funnel_country.melt(id_vars='країна', value_vars=['реєстрація', 'профіль_улюбленця', 'знижка_партнера']))
plt.title('Воронка Реєстрація -> Профіль -> Знижка')
plt.show()

######################################################################################################################## Task 4 - funnel View -> Booking -> Deal

active_listings = listings[listings['status'] == 'active']
bookings_confirmed = view_bookings[view_bookings['status'] == 'confirmed']

funnel_deal = pd.DataFrame([
    {'крок': '1. усі оголошення', 'кількість': listings['listing_id'].nunique()},
    {'крок': '2. активні', 'кількість': active_listings['listing_id'].nunique()},
    {'крок': '3. з переглядами', 'кількість': int((active_listings['view_count'] > 0).sum())},
    {'крок': '4. бронювання', 'кількість': view_bookings['booking_id'].nunique()},
    {'крок': '5. підтверджені броні', 'кількість': bookings_confirmed['booking_id'].nunique()},
    {'крок': '6. закриті угоди', 'кількість': deals['deal_id'].nunique()}])
funnel_deal['cr_крок_до_кроку_%'] = (funnel_deal['кількість'] / funnel_deal['кількість'].shift(1) * 100).round(2)
funnel_deal['cr_наскрізна_%'] = (funnel_deal['кількість'] / funnel_deal['кількість'].iloc[0] * 100).round(2)
print('--- Task 4: воронка Перегляд -> Бронювання -> Угода ---')
print(funnel_deal)

# the main loss point is booking cancellation, so we look at it separately
cancel_rate = (view_bookings['status'] == 'cancelled').mean()
print(f'частка скасованих броней: {cancel_rate:.2%}, угод із підтверджених броней: {len(deals) / len(bookings_confirmed):.2%}')

# segment: does paid listing promotion pay off
listing_deal['просування'] = np.where(listing_deal['amount_paid'].notna(), 'платне', 'без просування')
promo_segment = listing_deal.groupby('просування').agg(
    оголошення=('listing_id', 'nunique'),
    сер_перегляди=('view_count', 'mean'),
    бронювання=('booking_id', 'nunique'),
    угоди=('deal_id', 'nunique')).reset_index()
promo_segment['cr_оголошення_бронь_%'] = (promo_segment['бронювання'] / promo_segment['оголошення'] * 100).round(2)
promo_segment['сер_перегляди'] = promo_segment['сер_перегляди'].round(1)
print(promo_segment)

# segment: demand broken down by category
category_segment = listing_deal.merge(categories_df, on='category_id').groupby('category_name').agg(
    оголошення=('listing_id', 'nunique'),
    бронювання=('booking_id', 'nunique'),
    угоди=('deal_id', 'nunique'),
    сер_ціна=('price', 'mean')).reset_index()
category_segment['cr_оголошення_угода_%'] = (category_segment['угоди'] / category_segment['оголошення'] * 100).round(2)
category_segment['сер_ціна'] = category_segment['сер_ціна'].round(2)
print(category_segment.rename(columns={'category_name': 'категорія'}))

sns.barplot(x='крок', y='кількість', data=funnel_deal)
plt.xticks(rotation=20)
plt.title('Воронка Перегляд -> Бронювання -> Угода')
plt.show()

######################################################################################################################## Task 6 - comparison UA vs PL after the expansion

country_stat = listing_deal.groupby('країна').agg(
    оголошення=('listing_id', 'nunique'),
    бронювання=('booking_id', 'nunique'),
    угоди=('deal_id', 'nunique'),
    gmv=('deal_amount', 'sum')).reset_index()
country_stat = country_stat.merge(
    users.groupby('country')['user_id'].nunique().rename('користувачі').reset_index().rename(columns={'country': 'країна'}),
    on='країна')
country_stat['оголошень_на_користувача'] = (country_stat['оголошення'] / country_stat['користувачі']).round(2)
country_stat['cr_оголошення_угода_%'] = (country_stat['угоди'] / country_stat['оголошення'] * 100).round(2)
country_stat['сер_чек'] = (country_stat['gmv'] / country_stat['угоди']).round(2)
country_stat['gmv_на_користувача'] = (country_stat['gmv'] / country_stat['користувачі']).round(2)
print('--- Task 6: UA vs PL ---')
print(country_stat)

# GMV per user with zeros for those who sold nothing - otherwise the average will be inflated
gmv_by_seller = listing_deal.groupby('seller_id')['deal_amount'].sum()
users_gmv = users[['user_id', 'country']].copy()
users_gmv['gmv'] = users_gmv['user_id'].map(gmv_by_seller).fillna(0)

gmv_ua = users_gmv.loc[users_gmv['country'] == 'UA', 'gmv'].to_numpy()
gmv_pl = users_gmv.loc[users_gmv['country'] == 'PL', 'gmv'].to_numpy()

## bootstrap over 10000 iterations for the confidence interval of the GMV per user difference (UA - PL)
diff_distribution = []

for i in range(10000):
    sample_ua = np.random.choice(gmv_ua, size=len(gmv_ua), replace=True)
    sample_pl = np.random.choice(gmv_pl, size=len(gmv_pl), replace=True)
    diff = sample_ua.mean() - sample_pl.mean()
    diff_distribution.append(diff)

diff_distribution.sort()
quantile250 = diff_distribution[250]
quantile9750 = diff_distribution[9750]
print(f'95% ДІ різниці GMV на користувача (UA - PL): [{quantile250:.2f}, {quantile9750:.2f}]')
if quantile250 <= 0 <= quantile9750:
    print('нуль всередині інтервалу - ринки за GMV на користувача не відрізняються')
else:
    print('нуль поза інтервалом - різниця GMV на користувача між ринками значуща')

plt.hist(diff_distribution)
plt.axvline(quantile250, color='red', linestyle='--', label=f'quantile250 = {quantile250:.2f}')
plt.axvline(quantile9750, color='red', linestyle='--', label=f'quantile9750 = {quantile9750:.2f}')
plt.legend()
plt.title('Бутстреп різниці GMV на користувача, UA - PL')
plt.show()

# money sources: the marketplace earns on promotion and the fee, GMV is only the base for the take rate
revenue = pd.DataFrame([
    {'джерело': 'просування оголошень', 'сума': listing_promotions['amount_paid'].sum()},
    {'джерело': 'комісія за бронювання', 'сума': view_bookings['booking_fee'].sum()},
    {'джерело': 'GMV (обіг угод)', 'сума': deals['deal_amount'].sum()}])
print(revenue)
print(f"take rate за поточної монетизації: "
      f"{(listing_promotions['amount_paid'].sum() + view_bookings['booking_fee'].sum()) / deals['deal_amount'].sum():.2%}")

######################################################################################################################## data quality checks

# the deal amount must be related to the listing price; correlation close to zero = the data was generated independently
deal_vs_price = listing_deal.dropna(subset=['deal_amount'])[['deal_amount', 'price']].astype(float).corr().iloc[0, 1]
print(f'кореляція суми угоди і ціни оголошення: {deal_vs_price:.3f}')

# a deal cannot be closed earlier than the booking, and a booking - earlier than the listing creation
print(f"угод із closed_at раніше за created_at оголошення: "
      f"{(listing_deal['closed_at'] < listing_deal['created_at']).sum()}")

# deals are possible only from confirmed bookings
print(f"угод на скасованих бронях: {listing_deal[listing_deal['статус_броні'] == 'cancelled']['deal_id'].notna().sum()}")

# the clickstream covers only 3 user events - the product deal funnel is absent from the tracking
print(f"типи подій у клікстрімі: {sorted(clickstream_events['event_type'].unique())}")