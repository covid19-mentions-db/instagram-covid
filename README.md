# instagram-covid

<b>REQUIRED ENVIRONMENT VARIABLES</b>

\# Mongo DB to store posts
- `MONGODB_HOST`
- `MONGODB_PORT`
- `MONGODB_DB`
- `MONGODB_USER`
- `MONGODB_PASSWORD`
- `MONGODB_AUTH_DB`
- `MONGODB_RESULT_COLLECTION` - collection to store posts  

\# Proxy settings  
- `PROXIES_FILE_PATH_OR_URL` - may be url(calling it gives a list of proxies), filepath, empty(proxy won't be used)  
- `PROXIES_TYPE` - http(s), socks5, empty(when proxy is not used)  
 
\# If you use gitlab ci/cd(.gitlab-ci.yml is in the project) + kubernetes, you should also define:  
- `K8S_SERVER` - K8S api URL  
- `K8S_CERT` - K8S certificate  
- `K8S_TOKEN` - K8S token  
- `MOUNT_CONTAINER_PATH` - if PROXIES_FILE_PATH_OR_URL is filepath    
- `MOUNT_HOST_PATH` - if PROXIES_FILE_PATH_OR_URL is filepath, path in your kubernetes host  
## How to start parsing from scratch + specific ENVIRONMENT VARIABLES
- <b>parse_by_tag.py</b> - scrolls every pages by specified tag and extracts all the posts to DB, that older than `BORDER_TIME`
    - `TAG` (default - covid)
    - `BORDER_TIME` (default - 1575158400)  
- <b>parse_by_additional_posts_info.py</b> - gets addtitional information(`author_name`, `user_name`, `location`) for posts in DB  
    - `BATCH_COUNT` (default - 10000)  
    - `WORKER_COUNT` (default - 100)  
- <b>parse_post_coordinates_by_location_id.py</b> - gets `lat` and `lon` by `location_id`
    - `INSTAGRAM_LOCATION_COLLECTION` (default - instagram_location) - instagram locations cache  
    - `BATCH_COUNT` (default - 5000)  
    - `WORKER_COUNT` (default - 50)  
- <b>parse_post_languages.py</b> - gets `lang` for posts in DB  
    - `BATCH_COUNT` (default - 10000)  
- <b>parse_cronjob.py</b> - gets new posts for last DAYS_TO_DIG` days - used to keep data up to date  
    - `MAX_ITERATIONS_WITH_NO_NEW_POSTS` (default - 20)  
    - `DAYS_TO_DIG` (default - 3)  
