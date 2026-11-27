# Run all tests (cpu)
```
docker compose -f docker-compose.cpu.test.yml up -d --build
```
Once fully loads
```
    docker compose -f docker-compose.cpu.test.yml exec backend python -m unittest discover -s tests -p "test_*.py" -v
```

# Run all tests (gpu)
```
docker compose -f docker-compose.test.yml up -d --build
```
Once it fully loads
```
docker compose -f docker-compose.test.yml exec backend python -m unittest discover -s tests -p "test_*.py" -v
```