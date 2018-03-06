#!/bin/bash
# for crontab
#curl -i -H "apikey:b568de6800ad11e6bbdb009fcf461b12" -H "Content-Type:application/json" http://42.51.161.236/api/0b6f2d21fd4e11e590c4002feddfc315/plat/81dc04c7015511e6873d0059eed9d9af/execute -d '{"workflow_uuid":"a32993bd1b1511e6bf0f00029d52b92f","zone_uuid":[4,5],"name":"crontable2","cronExpression":[55,16,30,5]}'

# for exec by zone
#curl -i -H "apikey:b568de6800ad11e6bbdb009fcf461b12" -H "Content-Type:application/json" http://42.51.161.236/api/0b6f2d21fd4e11e590c4002feddfc315/plat/81dc04c7015511e6873d0059eed9d9af/execute -d '{"workflow_uuid":"a32993bd1b1511e6bf0f00029d52b92f","uuids":[5],"kind":"zone"}'

# for exec by host
curl -i -H "apikey:b568de6800ad11e6bbdb009fcf461b12" -H "Content-Type:application/json" http://42.51.161.236:90/api/0b6f2d21fd4e11e590c4002feddfc315/plat/81dc04c7015511e6873d0059eed9d9af/execute -d '{"workflow_uuid":"a32993bd1b1511e6bf0f00029d52b92f","uuids":[16],"kind":"host"}'
